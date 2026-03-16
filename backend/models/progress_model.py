import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Float, JSON, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import BaseModel, Field

from backend.database.db import Base


# ── SQLAlchemy ORM ──────────────────────────────────────────────────────────

class ProgressDB(Base):
    __tablename__ = "progress"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("user_profiles.id"), nullable=False)
    plan_id: Mapped[str] = mapped_column(String, ForeignKey("learning_plans.id"), nullable=False)
    completed_steps: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    total_steps: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    last_activity: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    streak_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class MessageDB(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("user_profiles.id"), nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)   # "user" | "assistant"
    content: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    context_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


# ── Pydantic Schemas ────────────────────────────────────────────────────────

class ProgressData(BaseModel):
    user_id: str
    plan_id: str
    completed_steps: list[str] = Field(default_factory=list)
    total_steps: int = 0
    percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    streak_days: int = 0

    model_config = {"from_attributes": True}


class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    role: str = Field(pattern="^(user|assistant)$")
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    context_snapshot: dict = Field(default_factory=dict)

    model_config = {"from_attributes": True}


class UserContext(BaseModel):
    user_id: str
    current_goals: list[str] = Field(default_factory=list)
    completed_topics: list[str] = Field(default_factory=list)
    learning_preferences: dict = Field(default_factory=dict)
    recent_interactions: list[str] = Field(default_factory=list)
    embedding_ids: list[str] = Field(default_factory=list)


class FeedbackReport(BaseModel):
    user_id: str
    plan_id: str
    summary: str
    strengths: list[str] = Field(default_factory=list)
    areas_for_improvement: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    is_delayed: bool = False
    generated_at: datetime = Field(default_factory=datetime.utcnow)
