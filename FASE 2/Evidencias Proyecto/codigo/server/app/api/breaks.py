"""Endpoint para registrar el regreso desde una pausa."""

from fastapi import APIRouter

from app.api.dependencies import CurrentUser, DatabaseSession
from app.schemas.sessions import BreakResponse, BreakUpdate
from app.services.sessions import end_break

router = APIRouter()


@router.patch("/{break_id}", response_model=BreakResponse)
def update_break(
    break_id: int,
    data: BreakUpdate,
    current_user: CurrentUser,
    database: DatabaseSession,
):
    """Registra el término de una pausa perteneciente al usuario."""
    return end_break(database, current_user.id, break_id, data.ended_at)
