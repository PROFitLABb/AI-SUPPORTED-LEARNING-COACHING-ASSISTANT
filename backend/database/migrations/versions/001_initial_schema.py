"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Enums ────────────────────────────────────────────────────────────────
    skill_level_enum = sa.Enum("beginner", "intermediate", "advanced", name="skill_level_enum")
    learning_style_enum = sa.Enum("visual", "reading", "hands-on", name="learning_style_enum")
    plan_status_enum = sa.Enum("active", "completed", "paused", name="plan_status_enum")
    step_status_enum = sa.Enum("pending", "in_progress", "completed", name="step_status_enum")
    resource_type_enum = sa.Enum("course", "article", "video", "book", name="resource_type_enum")

    skill_level_enum.create(op.get_bind(), checkfirst=True)
    learning_style_enum.create(op.get_bind(), checkfirst=True)
    plan_status_enum.create(op.get_bind(), checkfirst=True)
    step_status_enum.create(op.get_bind(), checkfirst=True)
    resource_type_enum.create(op.get_bind(), checkfirst=True)

    # ── users (user_profiles) ────────────────────────────────────────────────
    op.create_table(
        "user_profiles",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column(
            "skill_level",
            sa.Enum("beginner", "intermediate", "advanced", name="skill_level_enum"),
            nullable=False,
            server_default="beginner",
        ),
        sa.Column("interests", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column(
            "learning_style",
            sa.Enum("visual", "reading", "hands-on", name="learning_style_enum"),
            nullable=False,
            server_default="reading",
        ),
        sa.Column("weekly_hours", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    # ── learning_goals ───────────────────────────────────────────────────────
    op.create_table(
        "learning_goals",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("domain", sa.String(), nullable=False),
        sa.Column("target_level", sa.String(), nullable=False),
        sa.Column("timeline_weeks", sa.Integer(), nullable=False),
        sa.Column("sub_goals", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── learning_plans ───────────────────────────────────────────────────────
    op.create_table(
        "learning_plans",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("total_weeks", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("active", "completed", "paused", name="plan_status_enum"),
            nullable=False,
            server_default="active",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── learning_steps ───────────────────────────────────────────────────────
    op.create_table(
        "learning_steps",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("plan_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False, server_default=""),
        sa.Column("estimated_hours", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "in_progress", "completed", name="step_status_enum"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(["plan_id"], ["learning_plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── resources ────────────────────────────────────────────────────────────
    op.create_table(
        "resources",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("step_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column(
            "type",
            sa.Enum("course", "article", "video", "book", name="resource_type_enum"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(), nullable=False, server_default=""),
        sa.Column("estimated_hours", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("tags", sa.JSON(), nullable=False, server_default="[]"),
        sa.ForeignKeyConstraint(["step_id"], ["learning_steps.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── progress ─────────────────────────────────────────────────────────────
    op.create_table(
        "progress",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("plan_id", sa.String(), nullable=False),
        sa.Column("completed_steps", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("total_steps", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("percentage", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("last_activity", sa.DateTime(), nullable=False),
        sa.Column("streak_days", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plan_id"], ["learning_plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── messages ─────────────────────────────────────────────────────────────
    op.create_table(
        "messages",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("context_snapshot", sa.JSON(), nullable=False, server_default="{}"),
        sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("messages")
    op.drop_table("progress")
    op.drop_table("resources")
    op.drop_table("learning_steps")
    op.drop_table("learning_plans")
    op.drop_table("learning_goals")
    op.drop_table("user_profiles")

    # Drop enums
    sa.Enum(name="resource_type_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="step_status_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="plan_status_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="learning_style_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="skill_level_enum").drop(op.get_bind(), checkfirst=True)
