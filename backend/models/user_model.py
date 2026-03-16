import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, JSON, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import BaseModel, EmailStr, Field

from backend.database.db import Base


# ── SQLAlchemy ORM ──────────────────────────────────────────────────────────

class UserProfileDB(Base):
    __tablename__ = "user_profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    skill_level: Mapped[str] = mapped_column(
        SAEnum("beginner", "intermediate", "advanced", name="skill_level_enum"),
        nullable=False,
        default="beginner",
    )
    interests: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    learning_style: Mapped[str] = mapped_column(
        SAEnum("visual", "reading", "hands-on", name="learning_style_enum"),
        nullable=False,
        default="reading",
    )
    weekly_hours: Mapped[int] = mapped_column(nullable=False, default=5)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


# ── Pydantic Schemas ────────────────────────────────────────────────────────

class UserProfileCreate(BaseModel):
    name: str
    email: str
    skill_level: str = Field(default="beginner", pattern="^(beginner|intermediate|advanced)$")
    interests: list[str] = Field(default_factory=list)
    learning_style: str = Field(default="reading", pattern="^(visual|reading|hands-on)$")
    weekly_hours: int = Field(default=5, ge=1)


class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    skill_level: Optional[str] = Field(default=None, pattern="^(beginner|intermediate|advanced)$")
    interests: Optional[list[str]] = None
    learning_style: Optional[str] = Field(default=None, pattern="^(visual|reading|hands-on)$")
    weekly_hours: Optional[int] = Field(default=None, ge=1)


class UserProfileResponse(BaseModel):
    id: str
    name: str
    email: str
    skill_level: str
    interests: list[str]
    learning_style: str
    weekly_hours: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
