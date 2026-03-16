"""Analytics API routes."""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.db import get_db
from backend.models.learning_plan_model import LearningPlanDB, LearningStepDB
from backend.models.progress_model import ProgressDB, MessageDB

router = APIRouter(prefix="/analytics", tags=["analytics"])


class TimeDistribution(BaseModel):
    plan_id: str
    title: str
    estimated_hours: float
    completed_hours: float


class AnalyticsResponse(BaseModel):
    user_id: str
    progress_percentage: float
    completed_topics: list[str]
    time_distribution: list[TimeDistribution]
    streak_days: int = 0
    total_messages: int = 0
    active_plans: int = 0


def _calc_streak(messages: list) -> int:
    if not messages:
        return 0
    days = sorted({m.timestamp.date() for m in messages}, reverse=True)
    streak = 0
    today = datetime.utcnow().date()
    for i, day in enumerate(days):
        if day == today - timedelta(days=i):
            streak += 1
        else:
            break
    return streak


@router.get("/{user_id}", response_model=AnalyticsResponse)
async def get_analytics(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> AnalyticsResponse:
    # Mesaj geçmişi — streak ve toplam mesaj
    msg_result = await db.execute(
        select(MessageDB).where(MessageDB.user_id == user_id).order_by(MessageDB.timestamp)
    )
    messages = msg_result.scalars().all()
    streak_days = _calc_streak(messages)
    total_messages = len(messages)

    # Planlar
    plans_result = await db.execute(
        select(LearningPlanDB).where(LearningPlanDB.user_id == user_id)
    )
    plans = plans_result.scalars().all()
    active_plans = sum(1 for p in plans if p.status == "active")

    if not plans:
        return AnalyticsResponse(
            user_id=user_id,
            progress_percentage=0.0,
            completed_topics=[],
            time_distribution=[],
            streak_days=streak_days,
            total_messages=total_messages,
            active_plans=0,
        )

    plan_ids = [p.id for p in plans]

    progress_result = await db.execute(
        select(ProgressDB).where(
            ProgressDB.user_id == user_id,
            ProgressDB.plan_id.in_(plan_ids),
        )
    )
    progress_rows = {row.plan_id: row for row in progress_result.scalars().all()}

    percentages = [progress_rows[pid].percentage for pid in plan_ids if pid in progress_rows]
    overall_pct = sum(percentages) / len(percentages) if percentages else 0.0

    all_completed_step_ids: list[str] = []
    for row in progress_rows.values():
        all_completed_step_ids.extend(row.completed_steps or [])

    completed_topics: list[str] = []
    if all_completed_step_ids:
        steps_result = await db.execute(
            select(LearningStepDB).where(LearningStepDB.id.in_(all_completed_step_ids))
        )
        completed_topics = [s.title for s in steps_result.scalars().all()]

    time_distribution: list[TimeDistribution] = []
    for plan in plans:
        steps_result = await db.execute(
            select(LearningStepDB).where(LearningStepDB.plan_id == plan.id)
        )
        steps = steps_result.scalars().all()
        total_hours = sum(s.estimated_hours for s in steps)
        prog = progress_rows.get(plan.id)
        completed_ids = set(prog.completed_steps) if prog else set()
        completed_hours = sum(s.estimated_hours for s in steps if s.id in completed_ids)
        time_distribution.append(TimeDistribution(
            plan_id=plan.id,
            title=plan.title,
            estimated_hours=total_hours,
            completed_hours=completed_hours,
        ))

    return AnalyticsResponse(
        user_id=user_id,
        progress_percentage=round(overall_pct, 2),
        completed_topics=completed_topics,
        time_distribution=time_distribution,
        streak_days=streak_days,
        total_messages=total_messages,
        active_plans=active_plans,
    )
