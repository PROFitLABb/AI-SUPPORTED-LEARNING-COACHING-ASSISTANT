import uuid
from datetime import datetime
from sqlalchemy import String, Integer, JSON, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import BaseModel, Field

from backend.database.db import Base


# ── Pydantic Schema ─────────────────────────────────────────────────────────

class StructuredGoal(BaseModel):
    title: str
    domain: str                  # "programming", "data_science", vb.
    target_level: str = Field(pattern="^(beginner|intermediate|advanced)$")
    timeline_weeks: int = Field(ge=1)
    sub_goals: list[str] = Field(default_factory=list)


# ── SQLAlchemy ORM ──────────────────────────────────────────────────────────

class LearningGoalDB(Base):
    __tablename__ = "learning_goals"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("user_profiles.id"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    domain: Mapped[str] = mapped_column(String, nullable=False)
    target_level: Mapped[str] = mapped_column(String, nullable=False)
    timeline_weeks: Mapped[int] = mapped_column(Integer, nullable=False)
    sub_goals: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
