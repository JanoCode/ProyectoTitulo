"""Pruebas del modelo de datos definidas en CP-02-01 y CP-02-02."""

from sqlalchemy import CheckConstraint, DateTime, UniqueConstraint

from app.models import Base

EXPECTED_TABLES = {
    "applications",
    "breaks",
    "macro_actions",
    "macro_triggers",
    "macros",
    "settings",
    "usage_sessions",
    "users",
}


def test_cp_02_01_modelo_declara_las_ocho_tablas():
    """La metadata que consume Alembic contiene las ocho tablas acordadas."""
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_cp_02_02_claves_foraneas_eliminan_en_cascada():
    """Cada tabla dependiente elimina sus filas junto con la fila padre."""
    expected_foreign_keys = {
        "applications": ("user_id", "users.id"),
        "breaks": ("usage_session_id", "usage_sessions.id"),
        "macro_actions": ("macro_id", "macros.id"),
        "macro_triggers": ("macro_id", "macros.id"),
        "macros": ("user_id", "users.id"),
        "settings": ("user_id", "users.id"),
        "usage_sessions": ("user_id", "users.id"),
    }

    for table_name, (column_name, target) in expected_foreign_keys.items():
        foreign_key = next(iter(Base.metadata.tables[table_name].c[column_name].foreign_keys))
        assert foreign_key.target_fullname == target
        assert foreign_key.ondelete == "CASCADE"


def test_cp_02_02_settings_es_unica_y_tiene_valores_por_defecto():
    """Una cuenta tiene una configuración con los valores iniciales acordados."""
    table = Base.metadata.tables["settings"]
    unique_columns = {
        tuple(constraint.columns.keys())
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert ("user_id",) in unique_columns
    assert str(table.c.inactivity_break_minutes.server_default.arg) == "10"
    assert str(table.c.voice_enabled.server_default.arg) == "true"
    assert str(table.c.gesture_enabled.server_default.arg) == "true"


def test_cp_02_02_correos_y_aplicaciones_no_se_pueden_duplicar():
    """La base declara las dos reglas de unicidad del modelo acordado."""
    users = Base.metadata.tables["users"]
    applications = Base.metadata.tables["applications"]

    users_unique_columns = {
        tuple(constraint.columns.keys())
        for constraint in users.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    applications_unique_columns = {
        tuple(constraint.columns.keys())
        for constraint in applications.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert ("email",) in users_unique_columns
    assert ("user_id", "device_name", "name") in applications_unique_columns


def test_cp_02_02_tipos_de_macro_estan_restringidos():
    """Los tipos de disparador y acción tienen restricciones CHECK."""
    trigger_checks = {
        str(constraint.sqltext)
        for constraint in Base.metadata.tables["macro_triggers"].constraints
        if isinstance(constraint, CheckConstraint)
    }
    action_checks = {
        str(constraint.sqltext)
        for constraint in Base.metadata.tables["macro_actions"].constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert "trigger_type IN ('VOICE', 'GESTURE')" in trigger_checks
    assert any("MOUSE_CLICK" in check for check in action_checks)


def test_cp_02_02_fechas_conservan_zona_horaria():
    """Las fechas se traducen a timestamp with time zone en PostgreSQL."""
    timestamp_columns = [
        Base.metadata.tables["users"].c.created_at,
        Base.metadata.tables["usage_sessions"].c.started_at,
        Base.metadata.tables["usage_sessions"].c.ended_at,
        Base.metadata.tables["breaks"].c.started_at,
        Base.metadata.tables["breaks"].c.ended_at,
    ]

    assert all(isinstance(column.type, DateTime) for column in timestamp_columns)
    assert all(column.type.timezone for column in timestamp_columns)
