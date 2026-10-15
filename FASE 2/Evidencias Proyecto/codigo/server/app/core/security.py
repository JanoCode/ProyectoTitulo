"""Hash de contraseñas y creación y validación de tokens JWT."""

from datetime import UTC, datetime, timedelta
from enum import StrEnum
from uuid import uuid4

import bcrypt
import jwt

from app.core.config import get_settings


class TokenType(StrEnum):
    """Distingue los tokens breves de acceso de los tokens de renovación."""

    ACCESS = "access"
    REFRESH = "refresh"


def hash_password(password: str) -> str:
    """Genera un hash bcrypt con el costo 12 definido por la arquitectura."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode()


def verify_password(password: str, password_hash: str) -> bool:
    """Compara una contraseña sin recuperar ni almacenar su texto original."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_token(
    user_id: int,
    token_type: TokenType,
    *,
    now: datetime | None = None,
    lifetime: timedelta | None = None,
) -> str:
    """Firma un JWT con identidad, tipo, vencimiento e identificador único."""
    settings = get_settings()
    issued_at = now or datetime.now(UTC)
    if lifetime is None:
        lifetime = (
            timedelta(minutes=settings.access_token_minutes)
            if token_type is TokenType.ACCESS
            else timedelta(days=settings.refresh_token_days)
        )

    payload = {
        "sub": str(user_id),
        "type": token_type.value,
        "iat": issued_at,
        "exp": issued_at + lifetime,
        "jti": str(uuid4()),
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_value,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str, expected_type: TokenType) -> dict:
    """Valida firma y vencimiento, y comprueba el propósito del token."""
    settings = get_settings()
    payload = jwt.decode(
        token,
        settings.jwt_secret_value,
        algorithms=[settings.jwt_algorithm],
    )
    if payload.get("type") != expected_type.value:
        raise jwt.InvalidTokenError("Tipo de token incorrecto")
    return payload
