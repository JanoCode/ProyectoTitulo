"""Endpoint de la cuenta autenticada."""

from fastapi import APIRouter

from app.api.dependencies import CurrentUser
from app.schemas.auth import UserResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse)
def get_me(current_user: CurrentUser):
    """Devuelve la identidad contenida en el token de acceso."""
    return current_user
