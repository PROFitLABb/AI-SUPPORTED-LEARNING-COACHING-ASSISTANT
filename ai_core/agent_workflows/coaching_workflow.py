"""
CoachingWorkflow: CoachingAgent + UserContextMemory orkestrasyon.

Kullanıcı mesajlarını bağlamla zenginleştirerek koçluk yanıtları üretir.
"""
import logging
from typing import Any

from ai_core.memory.user_context_memory import UserContextMemory
from backend.agents.coaching_agent import CoachingAgent, CoachResponse
from backend.models.progress_model import Message, UserContext

logger = logging.getLogger(__name__)

_HISTORY_THRESHOLD = 20


class CoachingWorkflow:
    """CoachingAgent ve UserContextMemory'yi orkestre ederek koçluk oturumu yönetir."""

    def __init__(self, llm_client: Any, prompts: dict, context_memory: UserContextMemory) -> None:
        """
        Args:
            llm_client: OpenAI/Ollama uyumlu async LLM istemcisi.
            prompts: config/prompts.yaml içeriği (dict).
            context_memory: Kullanıcı bağlam belleği.
        """
        self._coaching_agent = CoachingAgent(llm_client=llm_client, prompts=prompts)
        self._context_memory = context_memory

    async def handle_message(
        self,
        user_id: str,
        message: str,
        history: list[Message],
    ) -> tuple[CoachResponse, list[Message]]:
        """Kullanıcı mesajını işler, gerekirse geçmişi özetler ve yanıt üretir.

        Args:
            user_id: Kullanıcı kimliği.
            message: Kullanıcının mesajı.
            history: Mevcut sohbet geçmişi.

        Returns:
            (CoachResponse, güncellenmiş_geçmiş) tuple'ı.
        """
        logger.info("CoachingWorkflow mesaj işleniyor (user_id=%s)", user_id)

        # Geçmiş eşiği aşıldıysa özetle
        if len(history) > _HISTORY_THRESHOLD:
            history, summary = await self._coaching_agent.maybe_summarize(history)
            if summary:
                logger.info("Sohbet geçmişi özetlendi (user_id=%s)", user_id)
                await self._context_memory.update_context(
                    user_id, {"recent_interactions": [f"[ÖZET] {summary}"]}
                )

        # Bağlamı getir
        context = await self._context_memory.get_context(user_id, message)

        # Yanıt üret
        response = await self._coaching_agent.respond(message, context)

        # Mesajı belleğe kaydet
        await self._context_memory.save_message(user_id, message, "user")
        await self._context_memory.save_message(user_id, response.content, "assistant")

        return response, history

    async def get_context(self, user_id: str, query: str = "") -> UserContext:
        """Kullanıcının mevcut bağlamını döndürür.

        Args:
            user_id: Kullanıcı kimliği.
            query: Bağlam araması için sorgu (opsiyonel).

        Returns:
            UserContext nesnesi.
        """
        return await self._context_memory.get_context(user_id, query)
