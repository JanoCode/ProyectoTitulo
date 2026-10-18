"""Crea las ocho tablas iniciales de ErgoSense.

Revision ID: 20261015_01
Revises:
Create Date: 2026-10-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261015_01"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Crea el esquema completo respetando dependencias entre tablas."""
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )

    op.create_table(
        "settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "inactivity_break_minutes",
            sa.Integer(),
            server_default=sa.text("10"),
            nullable=False,
        ),
        sa.Column(
            "voice_enabled",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "gesture_enabled",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_settings_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_settings")),
        sa.UniqueConstraint("user_id", name=op.f("uq_settings_user_id")),
    )

    op.create_table(
        "usage_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_usage_sessions_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_usage_sessions")),
    )
    op.create_index(
        op.f("ix_usage_sessions_user_id"),
        "usage_sessions",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "breaks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usage_session_id", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["usage_session_id"],
            ["usage_sessions.id"],
            name=op.f("fk_breaks_usage_session_id_usage_sessions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_breaks")),
    )
    op.create_index(
        op.f("ix_breaks_usage_session_id"),
        "breaks",
        ["usage_session_id"],
        unique=False,
    )

    op.create_table(
        "macros",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "enabled",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_macros_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_macros")),
    )
    op.create_index(
        op.f("ix_macros_user_id"),
        "macros",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "macro_triggers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("macro_id", sa.Integer(), nullable=False),
        sa.Column("trigger_type", sa.String(length=16), nullable=False),
        sa.Column("trigger_value", sa.Text(), nullable=False),
        sa.CheckConstraint(
            "trigger_type IN ('VOICE', 'GESTURE')",
            name=op.f("ck_macro_triggers_valid_trigger_type"),
        ),
        sa.ForeignKeyConstraint(
            ["macro_id"],
            ["macros.id"],
            name=op.f("fk_macro_triggers_macro_id_macros"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_macro_triggers")),
    )
    op.create_index(
        op.f("ix_macro_triggers_macro_id"),
        "macro_triggers",
        ["macro_id"],
        unique=False,
    )

    op.create_table(
        "macro_actions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("macro_id", sa.Integer(), nullable=False),
        sa.Column("action_type", sa.String(length=20), nullable=False),
        sa.Column("action_value", sa.Text(), nullable=False),
        sa.Column("execution_order", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "action_type IN "
            "('OPEN_URL', 'OPEN_APP', 'KEY_PRESS', 'TYPE_TEXT', 'MOUSE_CLICK')",
            name=op.f("ck_macro_actions_valid_action_type"),
        ),
        sa.ForeignKeyConstraint(
            ["macro_id"],
            ["macros.id"],
            name=op.f("fk_macro_actions_macro_id_macros"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_macro_actions")),
    )
    op.create_index(
        op.f("ix_macro_actions_macro_id"),
        "macro_actions",
        ["macro_id"],
        unique=False,
    )

    op.create_table(
        "applications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("device_name", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("executable_path", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_applications_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_applications")),
        sa.UniqueConstraint(
            "user_id",
            "device_name",
            "name",
            name="uq_applications_user_device_name",
        ),
    )
    op.create_index(
        op.f("ix_applications_user_id"),
        "applications",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Elimina el esquema en el orden inverso a sus dependencias."""
    op.drop_table("applications")
    op.drop_table("macro_actions")
    op.drop_table("macro_triggers")
    op.drop_table("macros")
    op.drop_table("breaks")
    op.drop_table("usage_sessions")
    op.drop_table("settings")
    op.drop_table("users")
