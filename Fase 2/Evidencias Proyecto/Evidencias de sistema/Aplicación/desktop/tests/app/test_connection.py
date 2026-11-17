import httpx
import pytest

from ergosense.api_client import ApiClient, ApiClientError
from ergosense.app import connection


@pytest.fixture
def configuration(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.delenv("ERGOSENSE_API_URL", raising=False)
    return connection.configuration_path()


def test_server_choice_survives_restart_and_environment_has_priority(configuration, monkeypatch):
    connection.save_server_url(" https://example.org/ ")
    assert connection.server_url() == "https://example.org/api/v1"
    monkeypatch.setenv("ERGOSENSE_API_URL", "http://127.0.0.1:18080/api/v1")
    assert connection.server_url() == "http://127.0.0.1:18080/api/v1"


@pytest.mark.parametrize("data", ["invalid", "[]", '{"api_url": 3}', '{}'])
def test_damaged_configuration_recovers_default(configuration, data):
    configuration.parent.mkdir(parents=True)
    configuration.write_text(data)
    assert connection.server_url() == connection.DEFAULT_API_URL


@pytest.mark.parametrize("url", [
    "file:///server", "https://user:password@example.org", "http://example.org:99999",
    "http://example.org:0", "https://example.org/api/v1?token=secret", "http://bad host",
    "https://example.org/other", "https://example.org/#fragment",
])
def test_server_rejects_unsafe_or_incomplete_addresses(url):
    with pytest.raises(ValueError):
        connection.normalize_api_url(url)


class Tokens:
    value = "previous-server-token"

    def clear(self):
        self.value = None


def test_changing_server_clears_credentials_and_does_not_send_them_to_health():
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={"status": "ok"})

    tokens = Tokens()
    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        client = ApiClient("https://old.example/api/v1", token_store=tokens, http_client=http)
        client._access_token = "private"
        client.user = {"id": 1}
        client.check_server("https://new.example/api/v1")
        assert tokens.value is not None
        assert "authorization" not in requests[0].headers
        client.change_server("https://new.example/api/v1")
        assert tokens.value is None
        assert client.user is None
        assert client._access_token is None


@pytest.mark.parametrize("payload", [{"status": "down"}, ["ok"], {"other": "service"}])
def test_server_check_rejects_another_application(payload):
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=payload))) as http:
        client = ApiClient("http://localhost/api/v1", http_client=http)
        with pytest.raises(ApiClientError):
            client.check_server("http://localhost/api/v1")
