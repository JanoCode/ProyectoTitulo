"""Modelo relacional completo de ErgoSense para el Sprint 02."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class User(Base):
    """Cuenta que posee configuraciones, sesiones, macros y aplicaciones."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    settings: Mapped[Setting] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )
    usage_sessions: Mapped[list[UsageSession]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    macros: Mapped[list[Macro]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    applications: Mapped[list[Application]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Setting(Base):
    """Preferencias únicas de un usuario."""

    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    inactivity_break_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=10,
        server_default=text("10"),
    )
    voice_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )
    gesture_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )

    user: Mapped[User] = relationship(back_populates="settings")


class UsageSession(Base):
    """Período durante el cual una cuenta utiliza ErgoSense."""

    __tablename__ = "usage_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user: Mapped[User] = relationship(back_populates="usage_sessions")
    breaks: Mapped[list[Break]] = relationship(
        back_populates="usage_session",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Break(Base):
    """Pausa por inactividad detectada dentro de una sesión de uso."""

    __tablename__ = "breaks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usage_session_id: Mapped[int] = mapped_column(
        ForeignKey("usage_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    usage_session: Mapped[UsageSession] = relationship(back_populates="breaks")


class Macro(Base):
    """Automatización configurada por un usuario."""

    __tablename__ = "macros"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )

    user: Mapped[User] = relationship(back_populates="macros")
    triggers: Mapped[list[MacroTrigger]] = relationship(
        back_populates="macro",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    actions: Mapped[list[MacroAction]] = relationship(
        back_populates="macro",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="MacroAction.execution_order",
    )


class MacroTrigger(Base):
    """Condición de voz o gesto que activa una macro."""

    __tablename__ = "macro_triggers"
    __table_args__ = (
        CheckConstraint(
            "trigger_type IN ('VOICE', 'GESTURE')",
            name="valid_trigger_type",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    macro_id: Mapped[int] = mapped_column(
        ForeignKey("macros.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    trigger_type: Mapped[str] = mapped_column(String(16), nullable=False)
    trigger_value: Mapped[str] = mapped_column(Text, nullable=False)

    macro: Mapped[Macro] = relationship(back_populates="triggers")


class MacroAction(Base):
    """Acción ejecutada por una macro en un orden definido."""

    __tablename__ = "macro_actions"
    __table_args__ = (
        CheckConstraint(
            "action_type IN "
            "('OPEN_URL', 'OPEN_APP', 'KEY_PRESS', 'TYPE_TEXT', 'MOUSE_CLICK')",
            name="valid_action_type",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    macro_id: Mapped[int] = mapped_column(
        ForeignKey("macros.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action_type: Mapped[str] = mapped_column(String(20), nullable=False)
    action_value: Mapped[str] = mapped_column(Text, nullable=False)
    execution_order: Mapped[int] = mapped_column(Integer, nullable=False)

    macro: Mapped[Macro] = relationship(back_populates="actions")


class Application(Base):
    """Programa registrado por un usuario en un dispositivo."""

    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "device_name",
            "name",
            name="uq_applications_user_device_name",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    device_name: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    executable_path: Mapped[str] = mapped_column(Text, nullable=False)

    user: Mapped[User] = relationship(back_populates="applications")
