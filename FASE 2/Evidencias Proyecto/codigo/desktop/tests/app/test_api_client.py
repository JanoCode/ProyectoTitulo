"""Pruebas del cliente HTTP, tokens protegidos y renovación automática."""

import json

import httpx

from ergosense.api_client import ApiClient


class MemoryTokenStore:
    def __init__(self):
        self.value = None

    def get(self):
        return self.value

    def save(self, token):
        self.value = token

    def clear(self):
        self.value = None


def response(request, status_code, data):
    return httpx.Response(status_code, json=data, request=request)


def test_login_guarda_refresh_y_mantiene_access_solo_en_memoria():
    store = MemoryTokenStore()

    def handler(request):
        return response(
            request,
            200,
            {
                "access_token": "access-1",
                "refresh_token": "refresh-1",
                "user": {"name": "Alejandro", "email": "a@example.com"},
                "settings": {"inactivity_break_minutes": 10},
            },
        )

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = ApiClient("http://test/api/v1", token_store=store, http_client=http_client)

    client.login("a@example.com", "clave123")

    assert store.value == "refresh-1"
    assert client.user["name"] == "Alejandro"


def test_una_respuesta_401_renueva_access_y_repite_una_sola_vez():
    store = MemoryTokenStore()
    store.value = "refresh-1"
    calls = []

    def handler(request):
        calls.append((request.url.path, request.headers.get("Authorization")))
        if request.url.path.endswith("/auth/refresh"):
            return response(request, 200, {"access_token": "access-2"})
        authorization = request.headers.get("Authorization")
        if authorization == "Bearer access-1":
            return response(request, 401, {"detail": "Token vencido"})
        return response(
            request,
            200,
            {
                "inactivity_break_minutes": 10,
                "voice_enabled": True,
                "gesture_enabled": True,
            },
        )

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = ApiClient("http://test/api/v1", token_store=store, http_client=http_client)
    client._access_token = "access-1"

    settings = client.get_settings()

    assert settings["inactivity_break_minutes"] == 10
    assert [path for path, _ in calls] == [
        "/api/v1/settings",
        "/api/v1/auth/refresh",
        "/api/v1/settings",
    ]


def test_cp_02_17_logout_elimina_el_token_del_equipo():
    store = MemoryTokenStore()
    store.value = "refresh-1"
    received_body = {}

    def handler(request):
        received_body.update(json.loads(request.content))
        return response(request, 200, {"message": "Sesión cerrada"})

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = ApiClient("http://test/api/v1", token_store=store, http_client=http_client)
    client._access_token = "access-1"

    client.logout()

    assert received_body == {"refresh_token": "refresh-1"}
    assert store.value is None


def test_reabrir_aplicacion_renueva_token_y_carga_la_cuenta():
    store = MemoryTokenStore()
    store.value = "refresh-guardado"

    def handler(request):
        if request.url.path.endswith("/auth/refresh"):
            return response(request, 200, {"access_token": "access-nuevo"})
        if request.url.path.endswith("/users/me"):
            return response(
                request,
                200,
                {"id": 1, "name": "Alejandro", "email": "a@example.com"},
            )
        return response(
            request,
            200,
            {
                "inactivity_break_minutes": 10,
                "voice_enabled": True,
                "gesture_enabled": True,
            },
        )

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = ApiClient("http://test/api/v1", token_store=store, http_client=http_client)

    assert client.restore_session() is True
    assert client.user["name"] == "Alejandro"
    assert client.settings["inactivity_break_minutes"] == 10
