"""Lectura y modificación de la configuración del usuario autenticado."""

from fastapi import APIRouter

from app.api.dependencies import CurrentUser, DatabaseSession
from app.schemas.auth import SettingResponse, SettingUpdateRequest
from app.services import settings as settings_service

router = APIRouter()


@router.get("", response_model=SettingResponse)
def get_settings(current_user: CurrentUser):
    """Carga el tiempo de inactividad y el estado de voz y gestos."""
    return current_user.settings


@router.patch("", response_model=SettingResponse)
def update_settings(
    changes: SettingUpdateRequest,
    current_user: CurrentUser,
    database: DatabaseSession,
):
    """Guarda el tiempo de inactividad y el estado de voz y gestos (PB-36 y PB-37).

    El usuario sale del token: cada cuenta solo puede modificar su configuración.
    """
    return settings_service.update_settings(database, current_user, changes)
