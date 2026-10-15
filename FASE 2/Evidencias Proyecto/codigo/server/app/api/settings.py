"""Lectura de la configuración perteneciente al usuario autenticado."""

from fastapi import APIRouter

from app.api.dependencies import CurrentUser
from app.schemas.auth import SettingResponse

router = APIRouter()


@router.get("", response_model=SettingResponse)
def get_settings(current_user: CurrentUser):
    """Carga el tiempo de inactividad y el estado de voz y gestos."""
    return current_user.settings
