"""Casos CP-03-11 y CP-03-13 a CP-03-15: configuración del usuario."""

import pytest

from app.models import Setting, User


def create_account_and_token(client, email: str) -> str:
    password = "clave123"
    client.post(
        "/api/v1/auth/register",
        json={"name": "Usuario de prueba", "email": email, "password": password},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    return response.json()["access_token"]


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def saved_setting(database, email: str) -> Setting:
    user = database.query(User).filter_by(email=email).one()
    database.refresh(user.settings)
    return user.settings


def test_cp_03_13_guarda_el_nuevo_tiempo_de_inactividad(client, database):
    headers = bearer(create_account_and_token(client, "tiempo@example.com"))

    response = client.patch(
        "/api/v1/settings", headers=headers, json={"inactivity_break_minutes": 15}
    )

    loaded = client.get("/api/v1/settings", headers=headers).json()
    assert response.status_code == 200
    assert response.json()["inactivity_break_minutes"] == 15
    assert loaded["inactivity_break_minutes"] == 15
    assert saved_setting(database, "tiempo@example.com").inactivity_break_minutes == 15


def test_cp_03_11_guarda_el_estado_de_voz_y_gestos(client):
    headers = bearer(create_account_and_token(client, "estado@example.com"))

    client.patch(
        "/api/v1/settings",
        headers=headers,
        json={"voice_enabled": False, "gesture_enabled": False},
    )

    # La configuración queda en el servidor: se conserva al reiniciar la aplicación.
    settings = client.get("/api/v1/settings", headers=headers).json()
    assert settings["voice_enabled"] is False
    assert settings["gesture_enabled"] is False


def test_solo_cambia_los_campos_enviados(client):
    headers = bearer(create_account_and_token(client, "parcial@example.com"))

    response = client.patch(
        "/api/v1/settings", headers=headers, json={"gesture_enabled": False}
    )

    assert response.json() == {
        "inactivity_break_minutes": 10,  # sigue el valor por defecto
        "voice_enabled": True,
        "gesture_enabled": False,
    }


@pytest.mark.parametrize("value", [0, -5, 2.5, "10", None, True])
def test_cp_03_14_rechaza_tiempos_no_validos_y_mantiene_el_anterior(client, value):
    headers = bearer(create_account_and_token(client, "invalido@example.com"))

    response = client.patch(
        "/api/v1/settings", headers=headers, json={"inactivity_break_minutes": value}
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Los datos enviados no son válidos."
    settings = client.get("/api/v1/settings", headers=headers).json()
    assert settings["inactivity_break_minutes"] == 10


def test_cp_03_14_acepta_un_minuto(client):
    headers = bearer(create_account_and_token(client, "minimo@example.com"))

    response = client.patch(
        "/api/v1/settings", headers=headers, json={"inactivity_break_minutes": 1}
    )

    assert response.status_code == 200
    assert response.json()["inactivity_break_minutes"] == 1


def test_cp_03_15_el_periodo_de_aviso_de_60_minutos_no_es_configurable(client):
    headers = bearer(create_account_and_token(client, "aviso@example.com"))

    response = client.patch(
        "/api/v1/settings",
        headers=headers,
        json={"inactivity_break_minutes": 5, "alert_minutes": 30},
    )

    # El campo desconocido hace fallar todo el cambio: tampoco se guardan los 5 minutos.
    assert response.status_code == 422
    settings = client.get("/api/v1/settings", headers=headers).json()
    assert settings["inactivity_break_minutes"] == 10
    assert "alert_minutes" not in settings


def test_rechaza_un_cambio_sin_datos(client):
    headers = bearer(create_account_and_token(client, "vacio@example.com"))

    assert client.patch("/api/v1/settings", headers=headers, json={}).status_code == 422


def test_requiere_iniciar_sesion(client):
    response = client.patch("/api/v1/settings", json={"gesture_enabled": False})

    assert response.status_code == 401


def test_cada_cuenta_modifica_solo_su_configuracion(client):
    owner = bearer(create_account_and_token(client, "duena@example.com"))
    other = bearer(create_account_and_token(client, "otra@example.com"))

    client.patch(
        "/api/v1/settings", headers=owner, json={"inactivity_break_minutes": 20}
    )

    settings = client.get("/api/v1/settings", headers=other).json()
    assert settings["inactivity_break_minutes"] == 10
