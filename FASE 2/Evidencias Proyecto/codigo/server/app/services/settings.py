"""Reglas de negocio de la configuración del usuario (PB-36 y PB-37)."""

from sqlalchemy.orm import Session

from app.models import Setting, User
from app.schemas.auth import SettingUpdateRequest


def update_settings(
    database: Session,
    user: User,
    changes: SettingUpdateRequest,
) -> Setting:
    """Aplica solo los campos enviados a la única configuración de la cuenta."""
    setting = user.settings
    # exclude_unset deja fuera lo que el cliente no envió: un PATCH no borra lo demás.
    for field, value in changes.model_dump(exclude_unset=True).items():
        setattr(setting, field, value)
    database.commit()
    return setting
