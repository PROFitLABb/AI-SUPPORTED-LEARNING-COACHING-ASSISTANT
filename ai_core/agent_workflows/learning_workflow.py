"""
LearningWorkflow: LearningAgent + GoalExtractor orkestrasyon.

Kullanıcının ham hedef metninden yapılandırılmış bir öğrenme planı oluşturur.
"""
import logging
from typing import Any

from backend.agents.learning_agent import LearningAgent
from backend.models.learning_goal_model import StructuredGoal
from backend.models.learning_plan_model import LearningPlan
from backend.models.user_model import UserProfileResponse
from backend.nlp.goal_extractor import GoalExtractor

logger = logging.getLogger(__name__)


class LearningWorkflow:
    """GoalExtractor ve LearningAgent'ı orkestre ederek uçtan uca plan oluşturur."""

    def __init__(self, llm_client: Any, prompts: dict) -> None:
        """
        Args:
            llm_client: OpenAI/Ollama uyumlu async LLM istemcisi.
            prompts: config/prompts.yaml içeriği (dict).
        """
        self._goal_extractor = GoalExtractor(llm_client=llm_client, prompts=prompts)
        self._learning_agent = LearningAgent(llm_client=llm_client, prompts=prompts)

    async def run(self, raw_goal: str, user_profile: UserProfileResponse) -> tuple[StructuredGoal, LearningPlan]:
        """Ham hedef metninden öğrenme planı oluşturur.

        Args:
            raw_goal: Kullanıcının ham hedef metni.
            user_profile: Kullanıcı profil verisi.

        Returns:
            (StructuredGoal, LearningPlan) tuple'ı.
        """
        logger.info("LearningWorkflow başlatıldı (user_id=%s)", user_profile.id)

        # 1. Hedefi yapılandır
        structured_goal = await self._goal_extractor.extract(raw_goal)
        logger.info("Hedef çıkarıldı: %s (domain=%s)", structured_goal.title, structured_goal.domain)

        # 2. Planı oluştur
        plan = await self._learning_agent.generate_plan(user_profile)
        logger.info("Plan oluşturuldu: %s (%d adım)", plan.title, len(plan.steps))

        return structured_goal, plan

    async def revise(self, plan: LearningPlan, feedback: str) -> LearningPlan:
        """Mevcut planı kullanıcı geri bildirimine göre revize eder.

        Args:
            plan: Revize edilecek plan.
            feedback: Kullanıcı geri bildirimi.

        Returns:
            Güncellenmiş LearningPlan.
        """
        logger.info("Plan revizyonu başlatıldı (plan_id=%s)", plan.id)
        revised = await self._learning_agent.revise_plan(plan, feedback)
        logger.info("Plan revize edildi: %s (%d adım)", revised.title, len(revised.steps))
        return revised
