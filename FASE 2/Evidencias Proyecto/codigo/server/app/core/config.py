"""Configuración del servidor obtenida desde variables de entorno."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

# Durante el desarrollo, el archivo .env está en la carpeta codigo, tres niveles
# sobre este archivo. En Docker, las variables inyectadas por Compose tienen
# prioridad y no es necesario copiar el archivo .env dentro de la imagen.
ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    """Valores del servidor que pueden cambiar entre instalaciones."""

    database_url: str | None = None
    postgres_db: str = "ergosense"
    postgres_user: str = "ergosense"
    postgres_password: SecretStr | None = None
    postgres_host: str = "db"
    postgres_port: int = 5432
    jwt_secret: SecretStr | None = None
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60
    refresh_token_days: int = 30
    login_max_attempts: int = 5
    login_block_minutes: int = 5
    environment: Literal["development", "test", "production"] = "development"

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def sqlalchemy_database_url(self) -> str:
        """Devuelve una URL válida sin escribir secretos en el código."""
        if self.database_url is not None:
            return self.database_url

        if self.postgres_password is None:
            raise ValueError(
                "Falta DATABASE_URL o POSTGRES_PASSWORD en las variables de entorno."
            )

        return URL.create(
            drivername="postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        ).render_as_string(hide_password=False)

    @property
    def jwt_secret_value(self) -> str:
        """Entrega la clave de firma y falla claramente si no fue configurada."""
        if self.jwt_secret is None:
            raise ValueError("Falta JWT_SECRET en las variables de entorno.")
        return self.jwt_secret.get_secret_value()


@lru_cache
def get_settings() -> Settings:
    """Crea la configuración una sola vez durante la vida del proceso."""
    return Settings()
