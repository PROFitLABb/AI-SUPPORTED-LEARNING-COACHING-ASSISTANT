"""ProgressTracker: records step completions and calculates progress percentages."""
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.learning_plan_model import LearningPlan
from backend.models.progress_model import ProgressData, ProgressDB


class ProgressTracker:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── helpers ──────────────────────────────────────────────────────────────

    async def _get_or_create_db_row(self, user_id: str, plan_id: str) -> ProgressDB:
        result = await self._db.execute(
            select(ProgressDB).where(
                ProgressDB.user_id == user_id,
                ProgressDB.plan_id == plan_id,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = ProgressDB(
                id=str(uuid.uuid4()),
                user_id=user_id,
                plan_id=plan_id,
                completed_steps=[],
                total_steps=0,
                percentage=0.0,
                last_activity=datetime.utcnow(),
                streak_days=0,
            )
            self._db.add(row)
            await self._db.flush()
        return row

    def _row_to_data(self, row: ProgressDB) -> ProgressData:
        return ProgressData(
            user_id=row.user_id,
            plan_id=row.plan_id,
            completed_steps=list(row.completed_steps),
            total_steps=row.total_steps,
            percentage=row.percentage,
            last_activity=row.last_activity,
            streak_days=row.streak_days,
        )

    # ── public API ────────────────────────────────────────────────────────────

    async def record_completion(
        self, user_id: str, plan_id: str, step_id: str
    ) -> ProgressData:
        """Mark *step_id* as completed and update the percentage.

        The resulting percentage is always >= the previous percentage.
        """
        row = await self._get_or_create_db_row(user_id, plan_id)

        completed: list[str] = list(row.completed_steps)
        if step_id not in completed:
            completed.append(step_id)

        row.completed_steps = completed
        row.last_activity = datetime.utcnow()

        # Recalculate percentage; total_steps may be 0 if not yet set
        if row.total_steps > 0:
            new_pct = min(100.0, len(completed) / row.total_steps * 100.0)
            # Guarantee monotonic increase
            row.percentage = max(row.percentage, new_pct)
        else:
            row.percentage = row.percentage  # unchanged

        await self._db.commit()
        await self._db.refresh(row)
        return self._row_to_data(row)

    async def get_progress(self, user_id: str, plan_id: str) -> ProgressData | None:
        """Return the current progress for a user/plan pair, or None if not found."""
        result = await self._db.execute(
            select(ProgressDB).where(
                ProgressDB.user_id == user_id,
                ProgressDB.plan_id == plan_id,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._row_to_data(row)

    def calculate_percentage(self, plan: LearningPlan, progress: ProgressData) -> float:
        """Return completion percentage (0.0–100.0) based on plan steps.

        Uses the plan's step list as the source of truth for total_steps so
        the result is always consistent with the current plan structure.
        """
        total = len(plan.steps)
        if total == 0:
            return 0.0
        completed = len(
            [s for s in plan.steps if s.id in progress.completed_steps]
        )
        return min(100.0, completed / total * 100.0)
