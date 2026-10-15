"""Operaciones de persistencia para cuentas y configuraciones."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Setting, User


def get_user_by_email(database: Session, email: str) -> User | None:
    """Obtiene una cuenta por el correo ya normalizado."""
    statement = (
        select(User)
        .where(User.email == email)
        .options(selectinload(User.settings))
    )
    return database.scalar(statement)


def get_user_by_id(database: Session, user_id: int) -> User | None:
    """Obtiene una cuenta y carga su configuración en la misma operación."""
    statement = (
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.settings))
    )
    return database.scalar(statement)


def add_user(
    database: Session,
    *,
    name: str,
    email: str,
    password_hash: str,
) -> User:
    """Prepara una cuenta con su única configuración por defecto."""
    user = User(name=name, email=email, password_hash=password_hash)
    user.settings = Setting()
    database.add(user)
    return user
