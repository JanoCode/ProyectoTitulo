"""Conexión de SQLAlchemy y sesiones de trabajo con PostgreSQL."""

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


@lru_cache
def get_session_factory():
    """Crea una sola fábrica de sesiones cuando la API realmente la necesita."""
    # La creación diferida permite importar la aplicación en pruebas que
    # reemplazan la base de datos sin exigir credenciales de PostgreSQL.
    engine = create_engine(
        get_settings().sqlalchemy_database_url,
        pool_pre_ping=True,
    )
    return sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )


def get_db() -> Generator[Session, None, None]:
    """Entrega una sesión y garantiza su cierre al terminar la solicitud."""
    database = get_session_factory()()
    try:
        yield database
    finally:
        database.close()
