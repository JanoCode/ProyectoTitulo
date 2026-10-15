"""Dependencias compartidas que autentican cada solicitud protegida."""

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import TokenType, decode_token
from app.models import User
from app.repositories.users import get_user_by_id

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,
)

DatabaseSession = Annotated[Session, Depends(get_db)]
BearerToken = Annotated[str | None, Depends(oauth2_scheme)]


def get_current_user(
    token: BearerToken,
    database: DatabaseSession,
) -> User:
    """Obtiene el usuario exclusivamente desde un token de acceso válido."""
    if token is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Debes iniciar sesión para realizar esta operación.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_token(token, TokenType.ACCESS)
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError) as error:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "El token de acceso no es válido o venció.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error

    user = get_user_by_id(database, user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "La cuenta ya no existe.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
