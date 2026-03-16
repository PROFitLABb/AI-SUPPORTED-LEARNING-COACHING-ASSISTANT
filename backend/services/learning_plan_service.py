"""LearningPlanService: CRUD operations for learning plans."""
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.learning_plan_model import (
    LearningPlan,
    LearningPlanDB,
    LearningStep,
    LearningStepDB,
    Resource,
    ResourceDB,
)


class LearningPlanService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── helpers ──────────────────────────────────────────────────────────────

    async def _load_steps(self, plan_id: str) -> list[LearningStep]:
        """Load steps (with resources) for a plan from the DB."""
        result = await self._db.execute(
            select(LearningStepDB)
            .where(LearningStepDB.plan_id == plan_id)
            .order_by(LearningStepDB.order)
        )
        step_rows = result.scalars().all()

        steps: list[LearningStep] = []
        for row in step_rows:
            res_result = await self._db.execute(
                select(ResourceDB).where(ResourceDB.step_id == row.id)
            )
            resources = [
                Resource.model_validate(r) for r in res_result.scalars().all()
            ]
            step = LearningStep(
                id=row.id,
                title=row.title,
                description=row.description,
                resources=resources,
                estimated_hours=row.estimated_hours,
                order=row.order,
                status=row.status,
                deadline=row.deadline,
            )
            steps.append(step)
        return steps

    def _row_to_plan(self, row: LearningPlanDB, steps: list[LearningStep]) -> LearningPlan:
        return LearningPlan(
            id=row.id,
            user_id=row.user_id,
            title=row.title,
            steps=steps,
            total_weeks=row.total_weeks,
            status=row.status,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    # ── public API ────────────────────────────────────────────────────────────

    async def create(self, user_id: str, plan: LearningPlan) -> LearningPlan:
        """Persist a LearningPlan (and its steps/resources) to the database."""
        plan_id = plan.id or str(uuid.uuid4())
        now = datetime.utcnow()

        db_plan = LearningPlanDB(
            id=plan_id,
            user_id=user_id,
            title=plan.title,
            total_weeks=plan.total_weeks,
            status=plan.status,
            created_at=now,
            updated_at=now,
        )
        self._db.add(db_plan)
        await self._db.flush()

        for step in plan.steps:
            step_id = step.id or str(uuid.uuid4())
            db_step = LearningStepDB(
                id=step_id,
                plan_id=plan_id,
                title=step.title,
                description=step.description,
                estimated_hours=step.estimated_hours,
                order=step.order,
                status=step.status,
                deadline=step.deadline,
            )
            self._db.add(db_step)
            await self._db.flush()

            for resource in step.resources:
                db_resource = ResourceDB(
                    id=resource.id or str(uuid.uuid4()),
                    step_id=step_id,
                    title=resource.title,
                    url=resource.url,
                    type=resource.type,
                    provider=resource.provider,
                    estimated_hours=resource.estimated_hours,
                    tags=resource.tags,
                )
                self._db.add(db_resource)

        await self._db.commit()
        await self._db.refresh(db_plan)

        steps = await self._load_steps(plan_id)
        return self._row_to_plan(db_plan, steps)

    async def get(self, plan_id: str) -> LearningPlan | None:
        """Retrieve a plan by ID, or None if not found."""
        result = await self._db.execute(
            select(LearningPlanDB).where(LearningPlanDB.id == plan_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        steps = await self._load_steps(plan_id)
        return self._row_to_plan(row, steps)

    async def update_step(self, plan_id: str, step_id: str, status: str) -> LearningPlan:
        """Update the status of a single step and return the refreshed plan."""
        result = await self._db.execute(
            select(LearningStepDB).where(
                LearningStepDB.id == step_id,
                LearningStepDB.plan_id == plan_id,
            )
        )
        step_row = result.scalar_one()
        step_row.status = status

        plan_result = await self._db.execute(
            select(LearningPlanDB).where(LearningPlanDB.id == plan_id)
        )
        plan_row = plan_result.scalar_one()
        plan_row.updated_at = datetime.utcnow()

        await self._db.commit()
        await self._db.refresh(plan_row)

        steps = await self._load_steps(plan_id)
        return self._row_to_plan(plan_row, steps)

    async def get_alternatives(self, plan_id: str) -> list[LearningPlan]:
        """Return alternative plans for the given plan.

        Placeholder for future LearningAgent integration — returns empty list.
        """
        return []

    async def list_by_user(self, user_id: str) -> list[LearningPlan]:
        """Return all plans belonging to a user."""
        result = await self._db.execute(
            select(LearningPlanDB).where(LearningPlanDB.user_id == user_id)
        )
        rows = result.scalars().all()
        plans: list[LearningPlan] = []
        for row in rows:
            steps = await self._load_steps(row.id)
            plans.append(self._row_to_plan(row, steps))
        return plans
