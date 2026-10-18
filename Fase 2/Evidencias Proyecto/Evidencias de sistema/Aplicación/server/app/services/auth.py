"""Reglas de registro, login, renovación y cierre de sesión."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from threading import Lock

import jwt
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    TokenType,
    create_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models import User
from app.repositories.users import add_user, get_user_by_email, get_user_by_id
from app.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    RegisterRequest,
    TokenPairResponse,
)


@dataclass
class LoginAttempt:
    """Conteo consecutivo y momento hasta el que una cuenta está bloqueada."""

    failures: int = 0
    blocked_until: datetime | None = None


class AuthenticationState:
    """Estado temporal que la arquitectura decidió mantener en memoria."""

    def __init__(self):
        self._attempts: dict[str, LoginAttempt] = {}
        self._revoked_refresh_tokens: dict[str, datetime] = {}
        self._lock = Lock()

    def is_blocked(self, email: str, now: datetime) -> bool:
        with self._lock:
            attempt = self._attempts.get(email)
            if attempt is None or attempt.blocked_until is None:
                return False
            if now >= attempt.blocked_until:
                self._attempts.pop(email, None)
                return False
            return True

    def register_failure(self, email: str, now: datetime) -> bool:
        """Registra un fallo y devuelve True cuando comienza el bloqueo."""
        settings = get_settings()
        with self._lock:
            attempt = self._attempts.setdefault(email, LoginAttempt())
            attempt.failures += 1
            if attempt.failures >= settings.login_max_attempts:
                attempt.blocked_until = now + timedelta(
                    minutes=settings.login_block_minutes
                )
                return True
            return False

    def reset_failures(self, email: str) -> None:
        with self._lock:
            self._attempts.pop(email, None)

    def revoke_refresh(self, token_id: str, expires_at: datetime) -> None:
        with self._lock:
            self._revoked_refresh_tokens[token_id] = expires_at

    def is_refresh_revoked(self, token_id: str, now: datetime) -> bool:
        with self._lock:
            expired = [
                saved_id
                for saved_id, expiry in self._revoked_refresh_tokens.items()
                if expiry <= now
            ]
            for saved_id in expired:
                self._revoked_refresh_tokens.pop(saved_id, None)
            return token_id in self._revoked_refresh_tokens

    def clear(self) -> None:
        """Aísla las pruebas automatizadas; no se usa en peticiones normales."""
        with self._lock:
            self._attempts.clear()
            self._revoked_refresh_tokens.clear()


authentication_state = AuthenticationState()


def register_user(database: Session, data: RegisterRequest) -> User:
    """Crea cuenta y configuración dentro de una sola transacción."""
    if get_user_by_email(database, data.email) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "El correo ya está registrado.")

    user = add_user(
        database,
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
    )
    try:
        database.commit()
    except IntegrityError as error:
        database.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "El correo ya está registrado.",
        ) from error

    database.refresh(user)
    return get_user_by_id(database, user.id)


def login_user(
    database: Session,
    data: LoginRequest,
    *,
    now: datetime | None = None,
) -> TokenPairResponse:
    """Valida credenciales, controla bloqueos y emite los dos JWT."""
    current_time = now or datetime.now(UTC)
    if authentication_state.is_blocked(data.email, current_time):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "El inicio de sesión está bloqueado durante 5 minutos.",
        )

    user = get_user_by_email(database, data.email)
    if user is None or not verify_password(data.password, user.password_hash):
        blocked = authentication_state.register_failure(data.email, current_time)
        if blocked:
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                "El inicio de sesión está bloqueado durante 5 minutos.",
            )
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "El correo o la contraseña son incorrectos.",
        )

    authentication_state.reset_failures(data.email)
    settings = get_settings()
    return TokenPairResponse(
        access_token=create_token(user.id, TokenType.ACCESS, now=current_time),
        refresh_token=create_token(user.id, TokenType.REFRESH, now=current_time),
        access_expires_in=settings.access_token_minutes * 60,
        user=user,
        settings=user.settings,
    )


def refresh_access_token(
    database: Session,
    refresh_token: str,
    *,
    now: datetime | None = None,
) -> AccessTokenResponse:
    """Entrega acceso nuevo si el token de renovación sigue vigente."""
    current_time = now or datetime.now(UTC)
    try:
        payload = decode_token(refresh_token, TokenType.REFRESH)
        user_id = int(payload["sub"])
        token_id = str(payload["jti"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError) as error:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "El token de renovación no es válido o venció.",
        ) from error

    if authentication_state.is_refresh_revoked(token_id, current_time):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "La sesión fue cerrada y no puede renovarse.",
        )
    if get_user_by_id(database, user_id) is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "La cuenta ya no existe.")

    settings = get_settings()
    return AccessTokenResponse(
        access_token=create_token(user_id, TokenType.ACCESS, now=current_time),
        access_expires_in=settings.access_token_minutes * 60,
    )


def revoke_refresh_token(refresh_token: str, current_user_id: int) -> None:
    """Revoca solamente el token de renovación de la sesión actual."""
    try:
        payload = decode_token(refresh_token, TokenType.REFRESH)
        user_id = int(payload["sub"])
        expires_at = datetime.fromtimestamp(payload["exp"], UTC)
        token_id = str(payload["jti"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError) as error:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "El token de renovación no es válido o venció.",
        ) from error

    if user_id != current_user_id:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "El token de renovación no pertenece a esta sesión.",
        )
    authentication_state.revoke_refresh(token_id, expires_at)
