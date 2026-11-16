"""Reglas de negocio de macros y aplicaciones registradas (PB-38 a PB-44)."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core import catalog
from app.models import Application, Macro, MacroAction, MacroTrigger
from app.repositories import macros as repository
from app.schemas.macros import ApplicationData, MacroData, TriggerData


def list_macros(database: Session, user_id: int) -> list[Macro]:
    return repository.list_macros(database, user_id)


def create_macro(database: Session, user_id: int, data: MacroData) -> Macro:
    """Crea la macro con sus activadores y acciones en una sola transacción."""
    triggers = validate_triggers(database, user_id, data.triggers, None)
    macro = Macro(user_id=user_id)
    _fill(macro, data, triggers)
    database.add(macro)
    database.commit()
    database.refresh(macro)
    return macro


def replace_macro(
    database: Session, user_id: int, macro_id: int, data: MacroData
) -> Macro:
    """Reemplaza la macro completa: así el orden de las acciones puede cambiar."""
    macro = _get_macro(database, user_id, macro_id)
    triggers = validate_triggers(database, user_id, data.triggers, macro_id)
    _fill(macro, data, triggers)
    database.commit()
    database.refresh(macro)
    return macro


def set_macro_enabled(
    database: Session, user_id: int, macro_id: int, enabled: bool
) -> Macro:
    macro = _get_macro(database, user_id, macro_id)
    macro.enabled = enabled
    database.commit()
    database.refresh(macro)
    return macro


def delete_macro(database: Session, user_id: int, macro_id: int) -> None:
    """La base elimina en cascada sus activadores y acciones."""
    database.delete(_get_macro(database, user_id, macro_id))
    database.commit()


def validate_triggers(
    database: Session,
    user_id: int,
    triggers: list[TriggerData],
    macro_id: int | None,
) -> list[tuple[str, str]]:
    """Comprueba los activadores y los devuelve listos para guardar (PB-39 y PB-44).

    Se rechazan los que no son válidos, los que coinciden con un comando o gesto
    predefinido, los repetidos y los que ya usa otra macro de la cuenta.
    """
    used = {
        (trigger.trigger_type, catalog.normalize_phrase(trigger.trigger_value)): name
        for trigger, name in repository.trigger_owners(database, user_id, macro_id)
    }
    cleaned, seen = [], set()
    for trigger in triggers:
        kind = trigger.trigger_type
        value = (
            catalog.clean_phrase(trigger.trigger_value)
            if kind == "VOICE"
            else trigger.trigger_value.strip()
        )
        error = catalog.trigger_error(kind, value)
        if error:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, error)
        conflict = catalog.trigger_conflict(kind, value)
        key = (kind, catalog.normalize_phrase(value))
        if conflict is None and key in used:
            conflict = f"Ese activador ya está asignado a la macro «{used[key]}»."
        if conflict is None and key in seen:
            conflict = "La macro tiene el mismo activador repetido."
        if conflict:
            raise HTTPException(status.HTTP_409_CONFLICT, conflict)
        seen.add(key)
        cleaned.append((kind, value))
    return cleaned


def _fill(macro: Macro, data: MacroData, triggers: list[tuple[str, str]]) -> None:
    macro.name = data.name
    macro.description = data.description
    macro.enabled = data.enabled
    # Las listas nuevas reemplazan a las anteriores; delete-orphan borra las viejas.
    macro.triggers = [
        MacroTrigger(trigger_type=kind, trigger_value=value) for kind, value in triggers
    ]
    # El orden de ejecución es la posición en la lista, empezando en 1 (PB-40).
    macro.actions = [
        MacroAction(
            action_type=action.action_type,
            # El texto a escribir se guarda tal cual, incluidos sus espacios.
            action_value=action.action_value
            if action.action_type == "TYPE_TEXT"
            else action.action_value.strip(),
            execution_order=position,
        )
        for position, action in enumerate(data.actions, start=1)
    ]


def _get_macro(database: Session, user_id: int, macro_id: int) -> Macro:
    macro = repository.get_macro_for_user(database, macro_id, user_id)
    if macro is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La macro no existe.")
    return macro


# ---------- aplicaciones registradas (PB-41)


def list_applications(
    database: Session, user_id: int, device_name: str
) -> list[Application]:
    return repository.list_applications(database, user_id, device_name.strip())


def create_application(
    database: Session, user_id: int, data: ApplicationData
) -> Application:
    _check_unique_name(database, user_id, data, None)
    application = Application(user_id=user_id, **data.model_dump())
    database.add(application)
    database.commit()
    database.refresh(application)
    return application


def update_application(
    database: Session, user_id: int, application_id: int, data: ApplicationData
) -> Application:
    application = _get_application(database, user_id, application_id)
    _check_unique_name(database, user_id, data, application_id)
    for field, value in data.model_dump().items():
        setattr(application, field, value)
    database.commit()
    database.refresh(application)
    return application


def delete_application(database: Session, user_id: int, application_id: int) -> None:
    database.delete(_get_application(database, user_id, application_id))
    database.commit()


def _check_unique_name(
    database: Session, user_id: int, data: ApplicationData, application_id: int | None
) -> None:
    same = repository.find_application(database, user_id, data.device_name, data.name)
    if same is not None and same.id != application_id:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Ya registraste una aplicación con ese nombre en este computador.",
        )


def _get_application(
    database: Session, user_id: int, application_id: int
) -> Application:
    application = repository.get_application_for_user(database, application_id, user_id)
    if application is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La aplicación no existe.")
    return application
