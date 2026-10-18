"""Endpoints de sesiones de uso y creación de sus pausas."""

from fastapi import APIRouter, status

from app.api.dependencies import CurrentUser, DatabaseSession
from app.schemas.sessions import (
    BreakCreate,
    BreakResponse,
    UsageSessionCreate,
    UsageSessionResponse,
    UsageSessionUpdate,
)
from app.services.sessions import (
    end_usage_session,
    start_break,
    start_usage_session,
)

router = APIRouter()


@router.post("", response_model=UsageSessionResponse, status_code=status.HTTP_201_CREATED)
def create_usage_session(
    data: UsageSessionCreate,
    current_user: CurrentUser,
    database: DatabaseSession,
):
    """Registra el inicio del monitoreo para la cuenta autenticada."""
    return start_usage_session(database, current_user.id, data.started_at)


@router.patch("/{session_id}", response_model=UsageSessionResponse)
def update_usage_session(
    session_id: int,
    data: UsageSessionUpdate,
    current_user: CurrentUser,
    database: DatabaseSession,
):
    """Registra el término de una sesión propia."""
    return end_usage_session(database, current_user.id, session_id, data.ended_at)


@router.post(
    "/{session_id}/breaks",
    response_model=BreakResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_break(
    session_id: int,
    data: BreakCreate,
    current_user: CurrentUser,
    database: DatabaseSession,
):
    """Asocia una pausa a una sesión propia que continúe abierta."""
    return start_break(database, current_user.id, session_id, data.started_at)
