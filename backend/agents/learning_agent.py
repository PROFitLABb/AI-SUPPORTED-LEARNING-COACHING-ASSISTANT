"""
LearningAgent: Kullanıcı profiline göre öğrenme planı oluşturur ve revize eder.
"""
import asyncio
import json
import logging
import uuid
from datetime import datetime, date, timedelta
from typing import Any

from backend.models.user_model import UserProfileResponse
from backend.models.learning_plan_model import LearningPlan, LearningStep, Resource

logger = logging.getLogger(__name__)

_RETRY_MAX = 3
_RETRY_BASE_DELAY = 1.0  # saniye


class LearningAgent:
    """LLM kullanarak öğrenme planı oluşturan ve revize eden ajan."""

    def __init__(self, llm_client: Any, prompts: dict) -> None:
        """
        Args:
            llm_client: OpenAI/Ollama uyumlu async LLM istemcisi.
            prompts: config/prompts.yaml içeriği (dict).
        """
        self._llm = llm_client
        self._prompts = prompts

    # ── Public API ────────────────────────────────────────────────────────────

    async def generate_plan(self, user_profile: UserProfileResponse) -> LearningPlan:
        """Kullanıcı profiline göre 3-10 adımlı öğrenme planı oluşturur.

        Args:
            user_profile: Kullanıcı profil verisi.

        Returns:
            3-10 adım içeren LearningPlan nesnesi.

        Raises:
            RuntimeError: Tüm LLM denemeleri başarısız olursa.
        """
        prompt_cfg = self._prompts.get("learning_plan", {})
        system_msg = prompt_cfg.get("system", "")
        user_template = prompt_cfg.get("user", "")
        user_msg = user_template.format(
            name=user_profile.name,
            skill_level=user_profile.skill_level,
            interests=", ".join(user_profile.interests),
            goals="",
            weekly_hours=user_profile.weekly_hours,
            learning_style=user_profile.learning_style,
        )

        last_exc: Exception | None = None
        for attempt in range(1, _RETRY_MAX + 1):
            try:
                response_text = await self._call_llm(system_msg, user_msg)
                plan = self._parse_plan(response_text, user_profile.id)
                return plan
            except Exception as exc:
                last_exc = exc
                logger.warning("LearningAgent generate_plan hatası (deneme %d/%d): %s", attempt, _RETRY_MAX, exc)

            if attempt < _RETRY_MAX:
                delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))
                await asyncio.sleep(delay)

        raise RuntimeError(
            f"LearningAgent: {_RETRY_MAX} denemeden sonra plan oluşturulamadı. Son hata: {last_exc}"
        )

    async def revise_plan(self, plan: LearningPlan, feedback: str) -> LearningPlan:
        """Kullanıcı geri bildirimine göre mevcut planı revize eder.

        Args:
            plan: Revize edilecek mevcut öğrenme planı.
            feedback: Kullanıcının geri bildirimi.

        Returns:
            Güncellenmiş LearningPlan nesnesi.

        Raises:
            RuntimeError: Tüm LLM denemeleri başarısız olursa.
        """
        system_msg = (
            "You are a learning plan revision expert. "
            "Given an existing learning plan and user feedback, revise the plan accordingly. "
            "Return a JSON object with the same structure as the original plan but with improvements. "
            "Keep the plan between 3 and 10 steps."
        )
        plan_json = plan.model_dump_json(indent=2)
        user_msg = f"Revise this learning plan based on the feedback.\n\nPlan:\n{plan_json}\n\nFeedback: {feedback}"

        last_exc: Exception | None = None
        for attempt in range(1, _RETRY_MAX + 1):
            try:
                response_text = await self._call_llm(system_msg, user_msg)
                revised = self._parse_plan(response_text, plan.user_id, existing_id=plan.id)
                return revised
            except Exception as exc:
                last_exc = exc
                logger.warning("LearningAgent revise_plan hatası (deneme %d/%d): %s", attempt, _RETRY_MAX, exc)

            if attempt < _RETRY_MAX:
                delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))
                await asyncio.sleep(delay)

        raise RuntimeError(
            f"LearningAgent: {_RETRY_MAX} denemeden sonra plan revize edilemedi. Son hata: {last_exc}"
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    async def _call_llm(self, system_msg: str, user_msg: str) -> str:
        """LLM'e istek gönderir ve metin yanıtı döndürür."""
        response = await self._llm.chat.completions.create(
            model=getattr(self._llm, "_model", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content

    def _parse_plan(self, response_text: str, user_id: str, existing_id: str | None = None) -> LearningPlan:
        """LLM JSON yanıtını LearningPlan nesnesine dönüştürür."""
        data = json.loads(response_text)

        raw_steps = data.get("steps", [])
        # 3-10 adım sınırını zorla
        raw_steps = raw_steps[:10]
        if len(raw_steps) < 3:
            raise ValueError(f"Plan en az 3 adım içermelidir, {len(raw_steps)} adım döndü.")

        steps: list[LearningStep] = []
        today = date.today()
        for i, s in enumerate(raw_steps):
            resources = [
                Resource(
                    id=str(uuid.uuid4()),
                    title=r.get("title", ""),
                    url=r.get("url", "#"),
                    type=r.get("type", "article"),
                    provider=r.get("provider", ""),
                    estimated_hours=float(r.get("estimated_hours", 1.0)),
                    tags=r.get("tags", []),
                )
                for r in s.get("resources", [])
            ]
            deadline_raw = s.get("deadline")
            if deadline_raw:
                try:
                    deadline = date.fromisoformat(str(deadline_raw))
                except ValueError:
                    deadline = today + timedelta(weeks=(i + 1))
            else:
                deadline = today + timedelta(weeks=(i + 1))

            steps.append(LearningStep(
                id=str(uuid.uuid4()),
                title=s.get("title", f"Adım {i + 1}"),
                description=s.get("description", ""),
                resources=resources,
                estimated_hours=float(s.get("estimated_hours", 2.0)),
                order=i + 1,
                status="pending",
                deadline=deadline,
            ))

        return LearningPlan(
            id=existing_id or str(uuid.uuid4()),
            user_id=user_id,
            title=data.get("title", "Öğrenme Planı"),
            steps=steps,
            total_weeks=int(data.get("total_weeks", len(steps))),
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
