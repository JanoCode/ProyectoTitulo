"""Consultas de macros y aplicaciones, siempre acotadas por usuario (RNF-13)."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Application, Macro, MacroTrigger


def list_macros(database: Session, user_id: int) -> list[Macro]:
    """Macros de la cuenta con sus activadores y acciones, en una sola carga."""
    statement = (
        select(Macro)
        .where(Macro.user_id == user_id)
        .options(selectinload(Macro.triggers), selectinload(Macro.actions))
        .order_by(Macro.id)
    )
    return list(database.scalars(statement))


def get_macro_for_user(database: Session, macro_id: int, user_id: int) -> Macro | None:
    """Filtra por id y usuario para no revelar macros de otra cuenta."""
    statement = select(Macro).where(Macro.id == macro_id, Macro.user_id == user_id)
    return database.scalar(statement)


def trigger_owners(
    database: Session, user_id: int, exclude_macro_id: int | None
) -> list[tuple[MacroTrigger, str]]:
    """Activadores de las demás macros de la cuenta, con el nombre de su macro.

    macro_triggers no tiene user_id, por eso la unicidad se valida aquí (PB-44).
    """
    statement = (
        select(MacroTrigger, Macro.name).join(Macro).where(Macro.user_id == user_id)
    )
    if exclude_macro_id is not None:
        statement = statement.where(Macro.id != exclude_macro_id)
    return [(trigger, name) for trigger, name in database.execute(statement)]


def list_applications(
    database: Session, user_id: int, device_name: str
) -> list[Application]:
    statement = (
        select(Application)
        .where(Application.user_id == user_id, Application.device_name == device_name)
        .order_by(Application.name)
    )
    return list(database.scalars(statement))


def get_application_for_user(
    database: Session, application_id: int, user_id: int
) -> Application | None:
    statement = select(Application).where(
        Application.id == application_id, Application.user_id == user_id
    )
    return database.scalar(statement)


def find_application(
    database: Session, user_id: int, device_name: str, name: str
) -> Application | None:
    statement = select(Application).where(
        Application.user_id == user_id,
        Application.device_name == device_name,
        Application.name == name,
    )
    return database.scalar(statement)
