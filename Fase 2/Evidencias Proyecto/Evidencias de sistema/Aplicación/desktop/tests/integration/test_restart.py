import os
import subprocess
import time
from uuid import uuid4

import httpx
import pytest

URL = os.environ.get("ERGOSENSE_TEST_API_URL")
CONTAINER = os.environ.get("ERGOSENSE_QA_API_CONTAINER")
pytestmark = pytest.mark.skipif(
    not URL or CONTAINER != "ergosense-qa-api-1",
    reason="Requiere contenedor aislado ergosense-qa-api-1",
)


def test_account_data_survives_api_restart():
    with httpx.Client(base_url=URL, timeout=5) as client:
        credentials = {"email": f"restart-{uuid4().hex}@example.com", "password": uuid4().hex}
        assert client.post("/auth/register", json={"name": "Reinicio QA", **credentials}).status_code == 201
        token = client.post("/auth/login", json=credentials).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        assert client.patch("/settings", headers=headers,
                            json={"inactivity_break_minutes": 13}).status_code == 200
        saved = client.post("/macros", headers=headers, json={
            "name": "Persistencia", "triggers": [
                {"trigger_type": "GESTURE", "trigger_value": "fist"}],
            "actions": [{"action_type": "TYPE_TEXT", "action_value": "Conservado"}],
        }).json()
        subprocess.run(["docker", "restart", "ergosense-qa-api-1"], check=True,
                       capture_output=True, timeout=30)
        deadline = time.monotonic() + 30
        while True:
            try:
                if client.get("/health").status_code == 200:
                    break
            except httpx.RequestError:
                pass
            assert time.monotonic() < deadline
            time.sleep(0.25)
        login = client.post("/auth/login", json=credentials).json()
        assert login["settings"]["inactivity_break_minutes"] == 13
        headers = {"Authorization": f"Bearer {login['access_token']}"}
        assert client.get("/macros", headers=headers).json() == [saved]
