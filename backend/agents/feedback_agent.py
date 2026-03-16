"""
FeedbackAgent: İlerleme verilerini değerlendirir ve gecikme tespiti yapar.
"""
import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from backend.models.learning_plan_model import LearningPlan
from backend.models.progress_model import ProgressData

logger = logging.getLogger(__name__)

_RETRY_MAX = 3
_RETRY_BASE_DELAY = 1.0


@dataclass
class FeedbackReport:
    summary: str
    strengths: list[str] = field(default_factory=list)
    improvements: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)


class FeedbackAgent:
    """İlerleme değerlendirmesi ve gecikme tespiti yapan ajan."""

    def __init__(self, llm_client: Any | None = None, prompts: dict | None = None) -> None:
        """
        Args:
            llm_client: OpenAI/Ollama uyumlu async LLM istemcisi (opsiyonel).
            prompts: config/prompts.yaml içeriği (dict, opsiyonel).
        """
        self._llm = llm_client
        self._prompts = prompts or {}

    # ── Public API ────────────────────────────────────────────────────────────

    async def evaluate_progress(self, progress: ProgressData) -> FeedbackReport:
        """İlerleme verilerini değerlendirip FeedbackReport oluşturur.

        Args:
            progress: Kullanıcının ilerleme verisi.

        Returns:
            FeedbackReport nesnesi.

        Raises:
            RuntimeError: LLM kullanılıyorsa ve tüm denemeler başarısız olursa.
        """
        if self._llm is None:
            return self._rule_based_evaluation(progress)

        system_msg = (
            "You are a learning progress evaluator. "
            "Analyze the user's learning progress and provide constructive feedback. "
            "Return a JSON object with: summary, strengths (list), improvements (list), next_actions (list)."
        )
        user_msg = (
            f"Evaluate this learning progress:\n"
            f"- Completed steps: {len(progress.completed_steps)} / {progress.total_steps}\n"
            f"- Completion percentage: {progress.percentage:.1f}%\n"
            f"- Streak days: {progress.streak_days}\n"
            f"- Last activity: {progress.last_activity.isoformat()}"
        )

        last_exc: Exception | None = None
        for attempt in range(1, _RETRY_MAX + 1):
            try:
                response = await self._llm.chat.completions.create(
                    model=getattr(self._llm, "_model", "gpt-4o-mini"),
                    messages=[
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": user_msg},
                    ],
                    response_format={"type": "json_object"},
                )
                data = json.loads(response.choices[0].message.content)
                return FeedbackReport(
                    summary=data.get("summary", ""),
                    strengths=data.get("strengths", []),
                    improvements=data.get("improvements", []),
                    next_actions=data.get("next_actions", []),
                )
            except Exception as exc:
                last_exc = exc
                logger.warning("FeedbackAgent evaluate_progress hatası (deneme %d/%d): %s", attempt, _RETRY_MAX, exc)

            if attempt < _RETRY_MAX:
                delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))
                await asyncio.sleep(delay)

        raise RuntimeError(
            f"FeedbackAgent: {_RETRY_MAX} denemeden sonra değerlendirme yapılamadı. Son hata: {last_exc}"
        )

    def detect_delay(self, plan: LearningPlan, progress: ProgressData) -> bool:
        """Kullanıcının beklenen ilerlemenin gerisinde olup olmadığını tespit eder.

        Beklenen ilerleme; planın başlangıcından bu yana geçen süreye göre
        tamamlanmış olması gereken adım yüzdesidir.

        Args:
            plan: Öğrenme planı.
            progress: Kullanıcının mevcut ilerleme verisi.

        Returns:
            True: Kullanıcı beklenen ilerlemenin gerisindeyse.
            False: Kullanıcı zamanında veya ilerideyse.
        """
        if plan.total_weeks <= 0 or progress.total_steps <= 0:
            return False

        now = datetime.utcnow()
        plan_start = plan.created_at
        elapsed_weeks = max(0.0, (now - plan_start).total_seconds() / (7 * 24 * 3600))

        # Beklenen tamamlanma yüzdesi
        expected_percentage = min(100.0, (elapsed_weeks / plan.total_weeks) * 100.0)

        return progress.percentage < expected_percentage

    # ── Private helpers ───────────────────────────────────────────────────────

    def _rule_based_evaluation(self, progress: ProgressData) -> FeedbackReport:
        """LLM olmadan kural tabanlı değerlendirme yapar."""
        pct = progress.percentage
        streak = progress.streak_days

        if pct >= 80:
            summary = "Harika ilerleme! Hedefinize çok yakınsınız."
            strengths = ["Yüksek tamamlanma oranı", "Tutarlı çalışma"]
            improvements: list[str] = []
            next_actions = ["Son adımları tamamlayın", "Öğrendiklerinizi pekiştirin"]
        elif pct >= 50:
            summary = "İyi gidiyorsunuz, devam edin!"
            strengths = ["Yarıdan fazlasını tamamladınız"]
            improvements = ["Tempoyu artırabilirsiniz"]
            next_actions = ["Bir sonraki adıma geçin", "Düzenli çalışma saatleri belirleyin"]
        elif pct >= 20:
            summary = "Başlangıç aşamasındasınız, motivasyonunuzu koruyun."
            strengths = ["Başladınız, bu önemli!"]
            improvements = ["Daha düzenli çalışma gerekiyor"]
            next_actions = ["Günlük küçük hedefler koyun", "Bir mentor veya çalışma arkadaşı bulun"]
        else:
            summary = "Henüz çok az ilerleme kaydedildi. Harekete geçme zamanı!"
            strengths: list[str] = []
            improvements = ["Düzenli çalışma alışkanlığı oluşturun"]
            next_actions = ["İlk adımı bugün tamamlayın", "Planınızı gözden geçirin"]

        if streak >= 7:
            strengths.append(f"{streak} günlük çalışma serisi - muhteşem!")

        return FeedbackReport(
            summary=summary,
            strengths=strengths,
            improvements=improvements,
            next_actions=next_actions,
        )
