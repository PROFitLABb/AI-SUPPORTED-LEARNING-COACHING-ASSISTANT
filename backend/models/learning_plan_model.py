import uuid
from datetime import datetime, date
from typing import Optional
from sqlalchemy import String, Float, Integer, JSON, DateTime, Date, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import BaseModel, Field

from backend.database.db import Base


# ── SQLAlchemy ORM ──────────────────────────────────────────────────────────

class LearningPlanDB(Base):
    __tablename__ = "learning_plans"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("user_profiles.id"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    total_weeks: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        SAEnum("active", "completed", "paused", name="plan_status_enum"),
        nullable=False,
        default="active",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class LearningStepDB(Base):
    __tablename__ = "learning_steps"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_id: Mapped[str] = mapped_column(String, ForeignKey("learning_plans.id"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False, default="")
    estimated_hours: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        SAEnum("pending", "in_progress", "completed", name="step_status_enum"),
        nullable=False,
        default="pending",
    )
    deadline: Mapped[Optional[date]] = mapped_column(Date, nullable=True)


class ResourceDB(Base):
    __tablename__ = "resources"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    step_id: Mapped[str] = mapped_column(String, ForeignKey("learning_steps.id"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(
        SAEnum("course", "article", "video", "book", name="resource_type_enum"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String, nullable=False, default="")
    estimated_hours: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)


# ── Pydantic Schemas ────────────────────────────────────────────────────────

class Resource(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    url: str
    type: str = Field(pattern="^(course|article|video|book)$")
    provider: str = ""
    estimated_hours: float = 0.0
    tags: list[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class LearningStep(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str = ""
    resources: list[Resource] = Field(default_factory=list)
    estimated_hours: float = 0.0
    order: int
    status: str = Field(default="pending", pattern="^(pending|in_progress|completed)$")
    deadline: Optional[date] = None

    model_config = {"from_attributes": True}


class LearningPlan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    steps: list[LearningStep] = Field(default_factory=list)
    total_weeks: int
    status: str = Field(default="active", pattern="^(active|completed|paused)$")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}


class LearningPlanCreate(BaseModel):
    user_id: str
    title: str
    total_weeks: int = Field(ge=1)
    steps: list[LearningStep] = Field(default_factory=list)


class LearningPlanResponse(BaseModel):
    id: str
    user_id: str
    title: str
    steps: list[LearningStep]
    total_weeks: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
