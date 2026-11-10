import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import httpx
import pytest

from ergosense.api_client import ApiClient, ApiClientError
from ergosense.api_client.pending import PendingQueue
from ergosense.app.remote_session import RemoteUsageSession
from ergosense.macros.library import MacroLibrary

URL = os.environ.get("ERGOSENSE_TEST_API_URL")
pytestmark = pytest.mark.skipif(not URL, reason="Requiere API de pruebas aislada")


class Tokens:
    def __init__(self):
        self.value = None

    def get(self):
        return self.value

    def save(self, value):
        self.value = value

    def clear(self):
        self.value = None


@pytest.fixture
def account():
    client = ApiClient(URL, token_store=Tokens())
    email, password = f"qa-{uuid4().hex}@example.com", uuid4().hex
    client.register("Prueba integrada", email, password)
    client.login(email, password)
    try:
        yield client, email, password
    finally:
        client.logout()
        client.close()


def test_settings_macros_and_device_applications_survive_new_login(account):
    first, email, password = account
    first.update_settings({"inactivity_break_minutes": 7, "voice_enabled": False,
                           "gesture_control_side": "left"})
    library = MacroLibrary(first, device="QA-A")
    library.save_application("Editor QA", r"C:\Windows\notepad.exe")
    macro = library.save_macro({
        "name": "Escribir saludo", "triggers": [
            {"trigger_type": "VOICE", "trigger_value": "escribir saludo"}],
        "actions": [{"action_type": "TYPE_TEXT", "action_value": "Hola"}],
    })
    second = ApiClient(URL, token_store=Tokens())
    try:
        second.login(email, password)
        assert second.settings["inactivity_break_minutes"] == 7
        assert second.settings["voice_enabled"] is False
        assert second.settings["gesture_control_side"] == "left"
        other_device = MacroLibrary(second, device="QA-B")
        other_device.load()
        assert other_device.find("VOICE", "escribir saludo")["id"] == macro["id"]
        assert other_device.application_path("Editor QA") is None
        same_device = MacroLibrary(second, device="QA-A")
        same_device.load()
        assert same_device.application_path("Editor QA") == r"C:\Windows\notepad.exe"
    finally:
        second.logout()
        second.close()


def test_records_recover_after_a_lost_post_response(account):
    client, _, _ = account
    original = client.start_usage_session
    lost = True
    now = datetime.now(UTC)

    def lose_response(started_at):
        nonlocal lost
        result = original(started_at)
        if lost:
            lost = False
            raise ApiClientError("Respuesta perdida")
        return result

    client.start_usage_session = lose_response
    clock = [0]
    pending = PendingQueue(client.check_connection, lambda: clock[0])
    remote = RemoteUsageSession(client, utc_clock=lambda: now, queue=pending)
    remote.start()
    remote.start_break(now + timedelta(minutes=10))
    remote.end_break(now + timedelta(minutes=11))
    assert pending.pending == 3
    clock[0] = 30
    pending.poll()
    assert pending.pending == 0
    assert remote._session.id is not None
    remote._utc_clock = lambda: now + timedelta(minutes=20)
    remote.close()
    assert pending.pending == 0


@pytest.mark.parametrize("path", ["/users/me", "/settings", "/macros", "/applications?device_name=QA-A"])
def test_live_api_rejects_requests_without_token(path):
    response = httpx.get(f"{URL}{path}", timeout=5)
    assert response.status_code == 401
