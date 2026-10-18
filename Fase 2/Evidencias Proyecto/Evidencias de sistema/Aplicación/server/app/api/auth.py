"""Endpoints públicos y protegidos de autenticación."""

from fastapi import APIRouter, status

from app.api.dependencies import CurrentUser, DatabaseSession
from app.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    TokenPairResponse,
)
from app.services.auth import (
    login_user,
    refresh_access_token,
    register_user,
    revoke_refresh_token,
)

router = APIRouter()


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(data: RegisterRequest, database: DatabaseSession):
    """Crea una cuenta y su configuración por defecto."""
    user = register_user(database, data)
    return RegisterResponse(user=user, settings=user.settings)


@router.post("/login", response_model=TokenPairResponse)
def login(data: LoginRequest, database: DatabaseSession):
    """Valida credenciales y entrega tokens de acceso y renovación."""
    return login_user(database, data)


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(data: RefreshRequest, database: DatabaseSession):
    """Genera acceso nuevo sin volver a solicitar la contraseña."""
    return refresh_access_token(database, data.refresh_token)


@router.post("/logout", response_model=MessageResponse)
def logout(
    data: RefreshRequest,
    current_user: CurrentUser,
):
    """Revoca el token persistente de esta sesión."""
    revoke_refresh_token(data.refresh_token, current_user.id)
    return MessageResponse(message="Sesión cerrada correctamente.")
