"""Endpoints de las aplicaciones registradas en cada computador (PB-41)."""

from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.api.dependencies import CurrentUser, DatabaseSession
from app.schemas.macros import ApplicationData, ApplicationResponse
from app.services import macros as service

router = APIRouter()


@router.get("", response_model=list[ApplicationResponse])
def list_applications(
    device_name: Annotated[str, Query(min_length=1, max_length=255)],
    current_user: CurrentUser,
    database: DatabaseSession,
):
    """Aplicaciones del computador indicado: la ruta depende de cada equipo."""
    return service.list_applications(database, current_user.id, device_name)


@router.post(
    "", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED
)
def create_application(
    data: ApplicationData, current_user: CurrentUser, database: DatabaseSession
):
    return service.create_application(database, current_user.id, data)


@router.put("/{application_id}", response_model=ApplicationResponse)
def update_application(
    application_id: int,
    data: ApplicationData,
    current_user: CurrentUser,
    database: DatabaseSession,
):
    return service.update_application(database, current_user.id, application_id, data)


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(
    application_id: int, current_user: CurrentUser, database: DatabaseSession
):
    service.delete_application(database, current_user.id, application_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
