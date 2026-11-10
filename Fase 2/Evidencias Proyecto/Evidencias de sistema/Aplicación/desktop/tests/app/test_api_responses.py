import httpx
import pytest

from ergosense.api_client import ApiClient, ApiClientError


@pytest.mark.parametrize("status, data", [(502, b"<html>error</html>"),
    (500, b"[]"), (422, b'{"detail":[{"input":"privado"}]}'), (200, b"incompleto")])
def test_invalid_response_is_a_controlled_error(status, data):
    transport = httpx.MockTransport(lambda request: httpx.Response(status, content=data))
    with httpx.Client(transport=transport) as http:
        client = ApiClient("http://test/api/v1", http_client=http)
        with pytest.raises(ApiClientError) as error:
            client._request("GET", "/health", authenticated=False)
    assert "privado" not in str(error.value)
