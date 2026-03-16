"""MoodleConnector: LMSAdapter implementation for Moodle REST API."""
import asyncio
import logging
from typing import Optional

import aiohttp

from backend.lms_integrations.custom_lms_adapter import LMSAdapter
from backend.models.progress_model import ProgressData
from backend.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class MoodleConnector(LMSAdapter):
    """Connects to a Moodle instance via its REST API (token-based auth).

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

    def _api_url(self, wsfunction: str) -> str:
        return (
            f"{self._base_url}/webservice/rest/server.php"
            f"?wstoken={self._token}&moodlewsrestformat=json&wsfunction={wsfunction}"
        )

    async def _get_fallback(self, user_id: str, error_msg: str) -> ProgressData:
        logger.error("Moodle error for user %s: %s", user_id, error_msg)
        await self._notification_service.send_lms_error(user_id, error_msg)
        if self._db_fallback is not None:
            return await self._db_fallback.get_progress(user_id)
        # Return empty progress when no fallback is available
        return ProgressData(user_id=user_id, plan_id="", total_steps=0, percentage=0.0)

    # ── LMSAdapter interface ────────────────────────────────────────────────

    async def get_progress(self, user_id: str) -> ProgressData:
        """Fetch user progress from Moodle; falls back to local DB on error."""
        url = self._api_url("core_completion_get_activities_completion_status")
        params = {"userid": user_id}
        timeout = aiohttp.ClientTimeout(total=self._timeout_seconds)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, params=params) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    statuses = data.get("statuses", [])
                    completed = [
                        str(s["cmid"])
                        for s in statuses
                        if s.get("state") == 1
                    ]
                    total = len(statuses)
                    percentage = (len(completed) / total * 100.0) if total else 0.0
                    return ProgressData(
                        user_id=user_id,
                        plan_id=str(data.get("courseid", "")),
                        completed_steps=completed,
                        total_steps=total,
                        percentage=percentage,
                    )
        except asyncio.TimeoutError:
            return await self._get_fallback(user_id, "Moodle isteği zaman aşımına uğradı (10s)")
        except aiohttp.ClientError as exc:
            return await self._get_fallback(user_id, str(exc))
        except Exception as exc:  # noqa: BLE001
            return await self._get_fallback(user_id, str(exc))

    async def sync_completion(self, user_id: str, course_id: str) -> bool:
        """Mark a course as complete in Moodle."""
        url = self._api_url("core_completion_update_activity_completion_status_manually")
        payload = {"cmid": course_id, "completed": 1}
        timeout = aiohttp.ClientTimeout(total=self._timeout_seconds)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, data=payload) as resp:
                    resp.raise_for_status()
                    return True
        except asyncio.TimeoutError:
            logger.error(
                "Moodle sync_completion timeout for user=%s course=%s", user_id, course_id
            )
            await self._notification_service.send_lms_error(
                user_id, "Tamamlama senkronizasyonu zaman aşımına uğradı"
            )
            return False
        except aiohttp.ClientError as exc:
            logger.error("Moodle sync_completion error: %s", exc)
            await self._notification_service.send_lms_error(user_id, str(exc))
            return False

    async def health_check(self) -> bool:
        """Return True if the Moodle site is reachable within the timeout."""
        url = self._api_url("core_webservice_get_site_info")
        timeout = aiohttp.ClientTimeout(total=self._timeout_seconds)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    return resp.status == 200
        except Exception:  # noqa: BLE001
            return False
