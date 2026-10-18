"""Esquemas para sesiones de uso y pausas por inactividad."""

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, field_validator


def to_utc(value: datetime | None) -> datetime | None:
    """Exige zona horaria y normaliza la fecha a UTC."""
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("La fecha debe incluir una zona horaria.")
    return value.astimezone(UTC)


class UsageSessionCreate(BaseModel):
    """Inicio de una sesión; si se omite la fecha, el servidor usa la actual."""

    started_at: datetime | None = None

    _normalize_started_at = field_validator("started_at")(to_utc)


class UsageSessionUpdate(BaseModel):
    """Término de una sesión de uso."""

    ended_at: datetime | None = None

    _normalize_ended_at = field_validator("ended_at")(to_utc)


class UsageSessionResponse(BaseModel):
    """Sesión almacenada, identificada por la cuenta del token."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    started_at: datetime
    ended_at: datetime | None


class BreakCreate(BaseModel):
    """Inicio de una pausa; normalmente corresponde a la última actividad."""

    started_at: datetime

    _normalize_started_at = field_validator("started_at")(to_utc)


class BreakUpdate(BaseModel):
    """Término de una pausa al regresar la actividad."""

    ended_at: datetime | None = None

    _normalize_ended_at = field_validator("ended_at")(to_utc)


class BreakResponse(BaseModel):
    """Pausa asociada a una sesión de uso."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    usage_session_id: int
    started_at: datetime
    ended_at: datetime | None
