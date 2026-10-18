"""Modelos que Alembic debe registrar en la metadata de SQLAlchemy."""

from app.models.base import Base
from app.models.entities import (
    Application,
    Break,
    Macro,
    MacroAction,
    MacroTrigger,
    Setting,
    UsageSession,
    User,
)

__all__ = [
    "Application",
    "Base",
    "Break",
    "Macro",
    "MacroAction",
    "MacroTrigger",
    "Setting",
    "UsageSession",
    "User",
]
