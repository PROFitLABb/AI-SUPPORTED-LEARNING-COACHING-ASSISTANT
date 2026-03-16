"""CanvasConnector: LMSAdapter implementation for Canvas LMS REST API."""
import asyncio
import logging
from typing import Optional

import aiohttp

from backend.lms_integrations.custom_lms_adapter import LMSAdapter
from backend.models.progress_model import ProgressData
from backend.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class CanvasConnector(LMSAdapter):
    """Connects to a Canvas LMS instance via its REST API (Bearer token auth).

    On connection failure or timeout the connector falls back to the last
    known progress stored in *db_fallback* and notifies the user via
    NotificationService.
    """

    def __init__(
        self,
        base_url: str,
        token: str,
        db_fallback=None,
        notification_service: Optional[NotificationService] = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._db_fallback = db_fallback
        self._notification_service = notification_service or NotificationService()

    # ── helpers ────────────────────────────────────────────────────────────

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._token}"}

    async def _get_fallback(self, user_id: str, error_msg: str) -> ProgressData:
        logger.error("Canvas error for user %s: %s", user_id, error_msg)
        await self._notification_service.send_lms_error(user_id, error_msg)
        if self._db_fallback is not None:
            return await self._db_fallback.get_progress(user_id)
        return ProgressData(user_id=user_id, plan_id="", total_steps=0, percentage=0.0)

    # ── LMSAdapter interface ────────────────────────────────────────────────

    async def get_progress(self, user_id: str) -> ProgressData:
        """Fetch user progress from Canvas; falls back to local DB on error."""
        # Canvas API: GET /api/v1/users/:user_id/enrollments
        url = f"{self._base_url}/api/v1/users/{user_id}/enrollments"
        timeout = aiohttp.ClientTimeout(total=self._timeout_seconds)
        try:
            async with aiohttp.ClientSession(
                headers=self._headers(), timeout=timeout
            ) as session:
                async with session.get(url) as resp:
                    resp.raise_for_status()
                    enrollments = await resp.json()
                    completed = [
                        str(e["course_id"])
                        for e in enrollments
                        if e.get("enrollment_state") == "completed"
                    ]
                    total = len(enrollments)
                    percentage = (len(completed) / total * 100.0) if total else 0.0
                    plan_id = str(enrollments[0]["course_id"]) if enrollments else ""
                    return ProgressData(
                        user_id=user_id,
                        plan_id=plan_id,
                        completed_steps=completed,
                        total_steps=total,
                        percentage=percentage,
                    )
        except asyncio.TimeoutError:
            return await self._get_fallback(user_id, "Canvas isteği zaman aşımına uğradı (10s)")
        except aiohttp.ClientError as exc:
            return await self._get_fallback(user_id, str(exc))
        except Exception as exc:  # noqa: BLE001
            return await self._get_fallback(user_id, str(exc))

    async def sync_completion(self, user_id: str, course_id: str) -> bool:
        """Mark a course as complete in Canvas via a submission."""
        # Canvas API: POST /api/v1/courses/:course_id/assignments/:assignment_id/submissions
        # Simplified: mark the course module as completed
        url = f"{self._base_url}/api/v1/courses/{course_id}/modules"
        timeout = aiohttp.ClientTimeout(total=self._timeout_seconds)
        try:
            async with aiohttp.ClientSession(
                headers=self._headers(), timeout=timeout
            ) as session:
                # Fetch modules and mark each as completed
                async with session.get(url) as resp:
                    resp.raise_for_status()
                    modules = await resp.json()

                for module in modules:
                    module_id = module.get("id")
                    complete_url = (
                        f"{self._base_url}/api/v1/courses/{course_id}"
                        f"/modules/{module_id}"
                    )
                    async with session.put(
                        complete_url, json={"module": {"state": "completed"}}
                    ) as put_resp:
                        put_resp.raise_for_status()
                return True
        except asyncio.TimeoutError:
            logger.error(
                "Canvas sync_completion timeout for user=%s course=%s", user_id, course_id
            )
            await self._notification_service.send_lms_error(
                user_id, "Tamamlama senkronizasyonu zaman aşımına uğradı"
            )
            return False
        except aiohttp.ClientError as exc:
            logger.error("Canvas sync_completion error: %s", exc)
            await self._notification_service.send_lms_error(user_id, str(exc))
            return False

    async def health_check(self) -> bool:
        """Return True if the Canvas API is reachable within the timeout."""
        url = f"{self._base_url}/api/v1/accounts"
        timeout = aiohttp.ClientTimeout(total=self._timeout_seconds)
        try:
            async with aiohttp.ClientSession(
                headers=self._headers(), timeout=timeout
            ) as session:
                async with session.get(url) as resp:
                    return resp.status == 200
        except Exception:  # noqa: BLE001
            return False
