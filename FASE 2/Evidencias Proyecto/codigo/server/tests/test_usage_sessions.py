"""Casos CP-02-08 y CP-02-21 para sesiones y pausas protegidas."""

from sqlalchemy import select

from app.models import Break, UsageSession


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


def test_cp_02_08_crea_y_cierra_una_sesion_del_usuario(client, database):
    token = create_account_and_token(client, "sesion@example.com")

    created = client.post(
        "/api/v1/usage-sessions",
        headers=bearer(token),
        json={"started_at": "2026-10-15T12:00:00Z"},
    )
    session_id = created.json()["id"]
    ended = client.patch(
        f"/api/v1/usage-sessions/{session_id}",
        headers=bearer(token),
        json={"ended_at": "2026-10-15T13:00:00Z"},
    )

    saved = database.get(UsageSession, session_id)
    assert created.status_code == 201
    assert ended.status_code == 200
    assert saved.user_id is not None
    assert saved.ended_at is not None


def test_solo_permite_una_sesion_abierta_por_usuario(client):
    token = create_account_and_token(client, "unica@example.com")
    headers = bearer(token)

    assert client.post("/api/v1/usage-sessions", headers=headers, json={}).status_code == 201
    assert client.post("/api/v1/usage-sessions", headers=headers, json={}).status_code == 409


def test_registra_inicio_y_termino_de_una_pausa(client, database):
    token = create_account_and_token(client, "pausa@example.com")
    headers = bearer(token)
    session_id = client.post(
        "/api/v1/usage-sessions",
        headers=headers,
        json={"started_at": "2026-10-15T12:00:00Z"},
    ).json()["id"]

    created = client.post(
        f"/api/v1/usage-sessions/{session_id}/breaks",
        headers=headers,
        json={"started_at": "2026-10-15T12:10:00Z"},
    )
    break_id = created.json()["id"]
    ended = client.patch(
        f"/api/v1/breaks/{break_id}",
        headers=headers,
        json={"ended_at": "2026-10-15T12:15:00Z"},
    )

    saved = database.get(Break, break_id)
    assert created.status_code == 201
    assert ended.status_code == 200
    assert saved.ended_at is not None


def test_cp_02_21_otro_usuario_recibe_404_y_no_modifica_recursos(client, database):
    owner_token = create_account_and_token(client, "owner@example.com")
    stranger_token = create_account_and_token(client, "stranger@example.com")
    created = client.post(
        "/api/v1/usage-sessions",
        headers=bearer(owner_token),
        json={"started_at": "2026-10-15T12:00:00Z"},
    )
    session_id = created.json()["id"]

    close_response = client.patch(
        f"/api/v1/usage-sessions/{session_id}",
        headers=bearer(stranger_token),
        json={"ended_at": "2026-10-15T13:00:00Z"},
    )
    break_response = client.post(
        f"/api/v1/usage-sessions/{session_id}/breaks",
        headers=bearer(stranger_token),
        json={"started_at": "2026-10-15T12:10:00Z"},
    )

    database.expire_all()
    saved = database.get(UsageSession, session_id)
    assert close_response.status_code == 404
    assert break_response.status_code == 404
    assert saved.ended_at is None
    assert database.scalars(select(Break)).all() == []
