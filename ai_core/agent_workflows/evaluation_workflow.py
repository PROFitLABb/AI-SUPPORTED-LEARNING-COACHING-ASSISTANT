"""
EvaluationWorkflow: FeedbackAgent + ProgressTracker orkestrasyon.

İlerleme verilerini değerlendirir, gecikme tespiti yapar ve geri bildirim raporu oluşturur.
"""
import logging
from typing import Any

from backend.agents.feedback_agent import FeedbackAgent, FeedbackReport
from backend.models.learning_plan_model import LearningPlan
from backend.models.progress_model import ProgressData

logger = logging.getLogger(__name__)


class ProgressTracker:
    """İlerleme yüzdesini hesaplayan yardımcı sınıf."""

    def calculate_percentage(self, plan: LearningPlan, progress: ProgressData) -> float:
        """Tamamlanan adımlara göre ilerleme yüzdesini hesaplar.

        Args:
            plan: Öğrenme planı.
            progress: Mevcut ilerleme verisi.

        Returns:
            0.0 - 100.0 arasında ilerleme yüzdesi.
        """
        total = len(plan.steps)
        if total == 0:
            return 0.0
        completed = len(progress.completed_steps)
        return min(100.0, (completed / total) * 100.0)

    def record_completion(self, progress: ProgressData, step_id: str) -> ProgressData:
        """Bir adımı tamamlandı olarak işaretler ve ilerlemeyi günceller.

        Args:
            progress: Mevcut ilerleme verisi.
            step_id: Tamamlanan adımın ID'si.

        Returns:
            Güncellenmiş ProgressData nesnesi.
        """
        if step_id not in progress.completed_steps:
            updated_steps = progress.completed_steps + [step_id]
            new_pct = (
                (len(updated_steps) / progress.total_steps * 100.0)
                if progress.total_steps > 0
                else 0.0
            )
            return progress.model_copy(update={
                "completed_steps": updated_steps,
                "percentage": min(100.0, new_pct),
            })
        return progress


class EvaluationWorkflow:
    """FeedbackAgent ve ProgressTracker'ı orkestre ederek ilerleme değerlendirmesi yapar."""

    def __init__(self, llm_client: Any | None = None, prompts: dict | None = None) -> None:
        """
        Args:
            llm_client: OpenAI/Ollama uyumlu async LLM istemcisi (opsiyonel).
            prompts: config/prompts.yaml içeriği (dict, opsiyonel).
        """
        self._feedback_agent = FeedbackAgent(llm_client=llm_client, prompts=prompts)
        self._progress_tracker = ProgressTracker()

    async def evaluate(
        self,
        plan: LearningPlan,
        progress: ProgressData,
    ) -> tuple[FeedbackReport, bool]:
        """İlerlemeyi değerlendirir ve gecikme durumunu kontrol eder.

        Args:
            plan: Öğrenme planı.
            progress: Kullanıcının ilerleme verisi.

        Returns:
            (FeedbackReport, is_delayed) tuple'ı.
        """
        logger.info(
            "EvaluationWorkflow başlatıldı (user_id=%s, plan_id=%s)",
            progress.user_id,
            progress.plan_id,
        )

        # İlerleme yüzdesini güncelle
        updated_pct = self._progress_tracker.calculate_percentage(plan, progress)
        if updated_pct != progress.percentage:
            progress = progress.model_copy(update={"percentage": updated_pct})

        # Gecikme tespiti
        is_delayed = self._feedback_agent.detect_delay(plan, progress)
        if is_delayed:
            logger.info("Gecikme tespit edildi (user_id=%s)", progress.user_id)

        # Geri bildirim raporu oluştur
        report = await self._feedback_agent.evaluate_progress(progress)

        return report, is_delayed

    def check_delay(self, plan: LearningPlan, progress: ProgressData) -> bool:
        """Gecikme durumunu senkron olarak kontrol eder.

        Args:
            plan: Öğrenme planı.
            progress: Kullanıcının ilerleme verisi.

        Returns:
            True: Gecikme varsa, False: Zamanında veya ilerideyse.
        """
        return self._feedback_agent.detect_delay(plan, progress)
