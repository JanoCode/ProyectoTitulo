"""Consultas de sesiones de uso y pausas, siempre acotadas por usuario."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Break, UsageSession


def get_open_session(database: Session, user_id: int) -> UsageSession | None:
    """Busca la única sesión que todavía no tiene hora de término."""
    statement = select(UsageSession).where(
        UsageSession.user_id == user_id,
        UsageSession.ended_at.is_(None),
    )
    return database.scalar(statement)


def get_session_for_user(
    database: Session,
    session_id: int,
    user_id: int,
) -> UsageSession | None:
    """Filtra por id y usuario para no revelar recursos de otra cuenta."""
    statement = select(UsageSession).where(
        UsageSession.id == session_id,
        UsageSession.user_id == user_id,
    )
    return database.scalar(statement)


def add_session(
    database: Session,
    *,
    user_id: int,
    started_at: datetime,
) -> UsageSession:
    session = UsageSession(user_id=user_id, started_at=started_at)
    database.add(session)
    return session


def get_open_break(database: Session, session_id: int) -> Break | None:
    """Busca una pausa sin terminar dentro de una sesión."""
    statement = select(Break).where(
        Break.usage_session_id == session_id,
        Break.ended_at.is_(None),
    )
    return database.scalar(statement)


def get_break_for_user(
    database: Session,
    break_id: int,
    user_id: int,
) -> Break | None:
    """Une con la sesión para asegurar que la pausa pertenezca al usuario."""
    statement = (
        select(Break)
        .join(UsageSession)
        .where(Break.id == break_id, UsageSession.user_id == user_id)
    )
    return database.scalar(statement)


def add_break(
    database: Session,
    *,
    session_id: int,
    started_at: datetime,
) -> Break:
    pause = Break(usage_session_id=session_id, started_at=started_at)
    database.add(pause)
    return pause
