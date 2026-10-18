"""Reglas de negocio de sesiones de uso y pausas por inactividad."""

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Break, UsageSession
from app.repositories.sessions import (
    add_break,
    add_session,
    get_break_for_user,
    get_open_break,
    get_open_session,
    get_session_for_user,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


def aware_utc(value: datetime) -> datetime:
    """SQLite pierde la zona en tests; PostgreSQL la conserva como timestamptz."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def start_usage_session(
    database: Session,
    user_id: int,
    started_at: datetime | None,
) -> UsageSession:
    """Crea una sesión solo si la cuenta no tiene otra abierta."""
    if get_open_session(database, user_id) is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Ya existe una sesión de uso en curso.",
        )
    session = add_session(
        database,
        user_id=user_id,
        started_at=started_at or utc_now(),
    )
    database.commit()
    database.refresh(session)
    return session


def end_usage_session(
    database: Session,
    user_id: int,
    session_id: int,
    ended_at: datetime | None,
) -> UsageSession:
    """Cierra una sesión propia; repetir la operación no duplica información."""
    session = get_session_for_user(database, session_id, user_id)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La sesión no existe.")
    if session.ended_at is not None:
        return session

    end_time = ended_at or utc_now()
    if aware_utc(end_time) < aware_utc(session.started_at):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "El término no puede ser anterior al inicio de la sesión.",
        )
    open_break = get_open_break(database, session.id)
    if open_break is not None:
        open_break.ended_at = end_time
    session.ended_at = end_time
    database.commit()
    database.refresh(session)
    return session


def start_break(
    database: Session,
    user_id: int,
    session_id: int,
    started_at: datetime,
) -> Break:
    """Registra una pausa únicamente en una sesión abierta del usuario."""
    session = get_session_for_user(database, session_id, user_id)
    if session is None or session.ended_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La sesión no existe.")
    if get_open_break(database, session.id) is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Ya existe una pausa en curso.",
        )
    if aware_utc(started_at) < aware_utc(session.started_at):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "La pausa no puede comenzar antes que la sesión.",
        )

    pause = add_break(database, session_id=session.id, started_at=started_at)
    database.commit()
    database.refresh(pause)
    return pause


def end_break(
    database: Session,
    user_id: int,
    break_id: int,
    ended_at: datetime | None,
) -> Break:
    """Cierra una pausa propia y permite repetir el PATCH de forma segura."""
    pause = get_break_for_user(database, break_id, user_id)
    if pause is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La pausa no existe.")
    if pause.ended_at is not None:
        return pause

    end_time = ended_at or utc_now()
    if aware_utc(end_time) < aware_utc(pause.started_at):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "El término no puede ser anterior al inicio de la pausa.",
        )
    pause.ended_at = end_time
    database.commit()
    database.refresh(pause)
    return pause
