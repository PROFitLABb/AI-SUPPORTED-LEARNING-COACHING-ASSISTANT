"""
CoachingAgent: Kullanıcı mesajlarına bağlama uygun koçluk yanıtları üretir.
"""
import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any

from backend.models.progress_model import UserContext, Message

logger = logging.getLogger(__name__)

_RETRY_MAX = 3
_RETRY_BASE_DELAY = 1.0
_HISTORY_THRESHOLD = 20  # Bu sayıyı aşınca otomatik özetleme tetiklenir


@dataclass
class CoachResponse:
    content: str
    suggested_resources: list[str] = field(default_factory=list)
    next_step_hint: str = ""


class CoachingAgent:
    """Koçluk yanıtları üreten ve sohbet geçmişini yöneten ajan."""

    def __init__(self, llm_client: Any, prompts: dict) -> None:
        """
        Args:
            llm_client: OpenAI/Ollama uyumlu async LLM istemcisi.
            prompts: config/prompts.yaml içeriği (dict).
        """
        self._llm = llm_client
        self._prompts = prompts

    # ── Public API ────────────────────────────────────────────────────────────

    async def respond(self, message: str, context: UserContext) -> CoachResponse:
        """Kullanıcı mesajına bağlama uygun koçluk yanıtı üretir.

        Args:
            message: Kullanıcının mesajı.
            context: Kullanıcının mevcut bağlamı.

        Returns:
            CoachResponse nesnesi.

        Raises:
            RuntimeError: Tüm LLM denemeleri başarısız olursa.
        """
        prompt_cfg = self._prompts.get("coaching_feedback", {})
        system_msg = prompt_cfg.get("system", "")
        user_template = prompt_cfg.get("user", "")
        user_msg = user_template.format(
            message=message,
            current_goals=", ".join(context.current_goals) or "Belirtilmemiş",
            completed_topics=", ".join(context.completed_topics) or "Henüz yok",
            recent_interactions="\n".join(context.recent_interactions[-5:]) or "Yok",
        )

        # Geçmiş eşiği aşıldıysa otomatik özetleme için uyarı logu
        if len(context.recent_interactions) > _HISTORY_THRESHOLD:
            logger.info(
                "Sohbet geçmişi eşiği aşıldı (%d > %d), özetleme önerilir.",
                len(context.recent_interactions),
                _HISTORY_THRESHOLD,
            )

        last_exc: Exception | None = None
        for attempt in range(1, _RETRY_MAX + 1):
            try:
                response_text = await self._call_llm(system_msg, user_msg)
                return self._parse_response(response_text)
            except Exception as exc:
                last_exc = exc
                logger.warning("CoachingAgent respond hatası (deneme %d/%d): %s", attempt, _RETRY_MAX, exc)

            if attempt < _RETRY_MAX:
                delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))
                await asyncio.sleep(delay)

        raise RuntimeError(
            f"CoachingAgent: {_RETRY_MAX} denemeden sonra yanıt üretilemedi. Son hata: {last_exc}"
        )

    async def summarize_history(self, history: list[Message]) -> str:
        """Sohbet geçmişini özetler. Özet orijinalden kısa ve boş olmayan olmalıdır.

        Sohbet geçmişi 20 mesajı aşınca bu metot otomatik olarak çağrılmalıdır.

        Args:
            history: Özetlenecek mesaj listesi.

        Returns:
            Sohbet geçmişinin özeti (boş olmayan string).

        Raises:
            RuntimeError: Tüm LLM denemeleri başarısız olursa.
        """
        if not history:
            return ""

        conversation = "\n".join(
            f"[{msg.role.upper()}]: {msg.content}" for msg in history
        )

        system_msg = (
            "You are a conversation summarizer. "
            "Summarize the following conversation concisely, capturing key topics, "
            "decisions, and user goals. The summary must be shorter than the original."
        )
        user_msg = f"Summarize this conversation:\n\n{conversation}"

        last_exc: Exception | None = None
        for attempt in range(1, _RETRY_MAX + 1):
            try:
                response = await self._llm.chat.completions.create(
                    model=getattr(self._llm, "_model", "gpt-4o-mini"),
                    messages=[
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": user_msg},
                    ],
                )
                summary = response.choices[0].message.content.strip()
                if summary:
                    return summary
                raise ValueError("LLM boş özet döndürdü.")
            except Exception as exc:
                last_exc = exc
                logger.warning("CoachingAgent summarize_history hatası (deneme %d/%d): %s", attempt, _RETRY_MAX, exc)

            if attempt < _RETRY_MAX:
                delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))
                await asyncio.sleep(delay)

        raise RuntimeError(
            f"CoachingAgent: {_RETRY_MAX} denemeden sonra özet oluşturulamadı. Son hata: {last_exc}"
        )

    async def maybe_summarize(self, history: list[Message]) -> tuple[list[Message], str]:
        """Geçmiş eşiği aşıyorsa özetler ve kısaltılmış geçmişi döndürür.

        Args:
            history: Mevcut sohbet geçmişi.

        Returns:
            (kısaltılmış_geçmiş, özet) tuple'ı. Eşik aşılmadıysa özet boş string.
        """
        if len(history) <= _HISTORY_THRESHOLD:
            return history, ""

        summary = await self.summarize_history(history)
        # Son 5 mesajı koru, gerisini özetle
        recent = history[-5:]
        return recent, summary

    # ── Private helpers ───────────────────────────────────────────────────────

    async def _call_llm(self, system_msg: str, user_msg: str) -> str:
        """LLM'e istek gönderir ve JSON metin yanıtı döndürür."""
        response = await self._llm.chat.completions.create(
            model=getattr(self._llm, "_model", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content

    def _parse_response(self, response_text: str) -> CoachResponse:
        """LLM JSON yanıtını CoachResponse nesnesine dönüştürür.

        JSON ayrıştırma başarısız olursa yanıtı düz metin olarak kullanır.
        """
        try:
            data = json.loads(response_text)
            return CoachResponse(
                content=data.get("content", response_text),
                suggested_resources=data.get("suggested_resources", []),
                next_step_hint=data.get("next_step_hint", ""),
            )
        except (json.JSONDecodeError, TypeError):
            return CoachResponse(content=response_text)
