"""Base SQLite aislada para probar la API sin tocar PostgreSQL del usuario."""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Estas variables se definen antes de importar app.main. Son exclusivas de tests.
os.environ["JWT_SECRET"] = "clave-exclusiva-para-pruebas-automatizadas"
os.environ["ENVIRONMENT"] = "test"

from app.core.config import get_settings
from app.core.database import get_db
from app.main import app
from app.models import Base
from app.services.auth import authentication_state

get_settings.cache_clear()


@pytest.fixture
def database():
    """Crea tablas nuevas para cada prueba y activa las FK de SQLite."""
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def client(database):
    """Reemplaza get_db para que todas las peticiones usen la base aislada."""
    def override_database():
        yield database

    authentication_state.clear()
    app.dependency_overrides[get_db] = override_database
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    authentication_state.clear()
