"""Casos CP-02-04 a CP-02-07 y CP-02-15 a CP-02-17 y CP-02-20."""

from datetime import timedelta

import pytest
from sqlalchemy import select

from app.core.security import TokenType, create_token, verify_password
from app.models import Setting, User


def register(client, email="alejandro@example.com", password="clave123"):
    return client.post(
        "/api/v1/auth/register",
        json={"name": "Alejandro", "email": email, "password": password},
    )


def login(client, email="alejandro@example.com", password="clave123"):
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )


def test_cp_02_04_cuenta_guarda_hash_y_no_la_contrasena(client, database):
    response = register(client)

    assert response.status_code == 201
    user = database.scalar(select(User))
    assert user.name == "Alejandro"
    assert user.email == "alejandro@example.com"
    assert user.password_hash != "clave123"
    assert verify_password("clave123", user.password_hash)
    assert user.created_at is not None


def test_cp_02_05_registro_crea_una_configuracion_por_defecto(client, database):
    register(client)

    saved_settings = database.scalars(select(Setting)).all()
    assert len(saved_settings) == 1
    assert saved_settings[0].inactivity_break_minutes == 10
    assert saved_settings[0].voice_enabled is True
    assert saved_settings[0].gesture_enabled is True


def test_cp_02_06_correo_duplicado_se_rechaza_sin_importar_mayusculas(client):
    assert register(client).status_code == 201
    duplicate = register(client, email="ALEJANDRO@example.com")

    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "El correo ya está registrado."


@pytest.mark.parametrize(
    "password",
    ["abc1234", "sololetras", "12345678"],
)
def test_cp_02_07_contrasenas_invalidas_no_crean_cuenta(client, database, password):
    response = register(client, password=password)

    assert response.status_code == 422
    assert database.scalar(select(User)) is None


def test_cp_02_07_ocho_caracteres_con_letras_y_numeros_es_valida(client):
    assert register(client, password="abcde123").status_code == 201


def test_cp_02_15_credenciales_invalidas_no_inician_sesion(client):
    register(client)

    response = login(client, password="incorrecta123")

    assert response.status_code == 401
    assert "incorrectos" in response.json()["detail"]


def test_cp_02_16_cinco_fallos_bloquean_incluso_la_clave_correcta(client):
    register(client)

    for _ in range(4):
        assert login(client, password="incorrecta123").status_code == 401
    assert login(client, password="incorrecta123").status_code == 429
    assert login(client).status_code == 429


def test_cp_02_17_logout_revoca_refresh_token(client):
    register(client)
    tokens = login(client).json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    logout = client.post(
        "/api/v1/auth/logout",
        headers=headers,
        json={"refresh_token": tokens["refresh_token"]},
    )
    refresh = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )

    assert logout.status_code == 200
    assert refresh.status_code == 401


def test_login_entrega_usuario_configuracion_y_tokens(client):
    register(client)

    response = login(client)

    assert response.status_code == 200
    body = response.json()
    assert body["user"]["email"] == "alejandro@example.com"
    assert body["settings"]["inactivity_break_minutes"] == 10
    assert body["access_token"]
    assert body["refresh_token"]


def test_refresh_entrega_un_token_de_acceso_nuevo(client):
    register(client)
    tokens = login(client).json()

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )

    assert response.status_code == 200
    assert response.json()["access_token"]


def test_cp_02_18_un_segundo_login_carga_la_misma_configuracion(client):
    register(client)
    first_login = login(client).json()
    second_login = login(client).json()

    response = client.get(
        "/api/v1/settings",
        headers={"Authorization": f"Bearer {second_login['access_token']}"},
    )

    assert first_login["user"]["id"] == second_login["user"]["id"]
    assert response.status_code == 200
    assert response.json() == first_login["settings"]


def test_cp_02_20_rechaza_token_ausente_alterado_y_vencido(client, database):
    register(client)
    user = database.scalar(select(User))
    valid_token = create_token(user.id, TokenType.ACCESS)
    expired_token = create_token(
        user.id,
        TokenType.ACCESS,
        lifetime=timedelta(seconds=-1),
    )

    assert client.get("/api/v1/users/me").status_code == 401
    assert (
        client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {valid_token}alterado"},
        ).status_code
        == 401
    )
    assert (
        client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        ).status_code
        == 401
    )
