"""Endpoints de macros con sus activadores y acciones (PB-38 a PB-40, PB-43)."""

from fastapi import APIRouter, Response, status

from app.api.dependencies import CurrentUser, DatabaseSession
from app.schemas.macros import MacroData, MacroResponse, MacroStateUpdate
from app.services import macros as service

router = APIRouter()


@router.get("", response_model=list[MacroResponse])
def list_macros(current_user: CurrentUser, database: DatabaseSession):
    """Macros de la cuenta: están disponibles en cualquier computador (PB-38)."""
    return service.list_macros(database, current_user.id)


@router.post("", response_model=MacroResponse, status_code=status.HTTP_201_CREATED)
def create_macro(data: MacroData, current_user: CurrentUser, database: DatabaseSession):
    return service.create_macro(database, current_user.id, data)


@router.put("/{macro_id}", response_model=MacroResponse)
def replace_macro(
    macro_id: int, data: MacroData, current_user: CurrentUser, database: DatabaseSession
):
    return service.replace_macro(database, current_user.id, macro_id, data)


@router.patch("/{macro_id}", response_model=MacroResponse)
def update_macro_state(
    macro_id: int,
    data: MacroStateUpdate,
    current_user: CurrentUser,
    database: DatabaseSession,
):
    return service.set_macro_enabled(database, current_user.id, macro_id, data.enabled)


@router.delete("/{macro_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_macro(macro_id: int, current_user: CurrentUser, database: DatabaseSession):
    service.delete_macro(database, current_user.id, macro_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
