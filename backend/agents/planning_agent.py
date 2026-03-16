"""
PlanningAgent: Öğrenme planından haftalık program oluşturur.
"""
import logging
from dataclasses import dataclass, field
from math import ceil

from backend.models.learning_plan_model import LearningPlan

logger = logging.getLogger(__name__)


@dataclass
class Schedule:
    user_id: str
    weekly_schedule: dict = field(default_factory=dict)
    total_weeks: int = 0


class PlanningAgent:
    """Öğrenme planını kullanıcının müsaitlik durumuna göre haftalık programa dönüştüren ajan."""

    def create_schedule(self, plan: LearningPlan, availability: dict) -> Schedule:
        """Öğrenme planından haftalık program oluşturur.

        Args:
            plan: Öğrenme planı.
            availability: Kullanıcının haftalık müsaitlik bilgisi.
                Örnek: {"monday": 2, "wednesday": 1.5, "saturday": 3}
                Değerler saatlik çalışma süresini temsil eder.

        Returns:
            Schedule nesnesi; weekly_schedule her hafta için adım listesi içerir.
        """
        weekly_hours = self._calculate_weekly_hours(availability)

        if weekly_hours <= 0:
            logger.warning("Haftalık müsaitlik sıfır veya negatif, varsayılan 5 saat kullanılıyor.")
            weekly_hours = 5.0

        weekly_schedule: dict[str, list[dict]] = {}
        current_week = 1
        hours_used_this_week = 0.0

        for step in sorted(plan.steps, key=lambda s: s.order):
            remaining_hours = step.estimated_hours if step.estimated_hours > 0 else 1.0

            while remaining_hours > 0:
                week_key = f"week_{current_week}"
                if week_key not in weekly_schedule:
                    weekly_schedule[week_key] = []

                available = weekly_hours - hours_used_this_week
                if available <= 0:
                    current_week += 1
                    hours_used_this_week = 0.0
                    continue

                allocated = min(remaining_hours, available)
                weekly_schedule[week_key].append({
                    "step_id": step.id,
                    "step_title": step.title,
                    "allocated_hours": round(allocated, 2),
                    "status": step.status,
                })
                hours_used_this_week += allocated
                remaining_hours -= allocated

                if hours_used_this_week >= weekly_hours:
                    current_week += 1
                    hours_used_this_week = 0.0

        total_weeks = max(current_week, plan.total_weeks)

        return Schedule(
            user_id=plan.user_id,
            weekly_schedule=weekly_schedule,
            total_weeks=total_weeks,
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _calculate_weekly_hours(self, availability: dict) -> float:
        """Müsaitlik dict'inden toplam haftalık saati hesaplar.

        Availability dict'i iki formatta olabilir:
        1. {"monday": 2, "wednesday": 1.5} - gün bazlı saatler
        2. {"weekly_hours": 10} - doğrudan haftalık saat
        """
        if "weekly_hours" in availability:
            return float(availability["weekly_hours"])

        day_keys = {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}
        total = sum(
            float(v) for k, v in availability.items()
            if k.lower() in day_keys and isinstance(v, (int, float))
        )
        return total
