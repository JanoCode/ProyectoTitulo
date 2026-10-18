"""Base declarativa compartida por todos los modelos SQLAlchemy."""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Los nombres estables permiten que Alembic cree y elimine restricciones de
# forma predecible en todas las instalaciones.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Clase de la que heredan las ocho entidades persistentes."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
