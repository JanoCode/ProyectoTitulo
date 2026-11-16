from datetime import timedelta

import pytest

from app.core.security import TokenType, create_token
from tests.test_macros import APPLICATIONS, MACROS, application, macro
from tests.test_usage_sessions import bearer, create_account_and_token


@pytest.mark.parametrize("path", ["/users/me", "/settings", "/macros", "/applications?device_name=QA"])
@pytest.mark.parametrize("token", ["invalid", "expired", "refresh"])
def test_all_resources_require_a_valid_access_token(client, path, token):
    if token == "expired":
        token = create_token(1, TokenType.ACCESS, lifetime=timedelta(seconds=-1))
    elif token == "refresh":
        token = create_token(1, TokenType.REFRESH)
    assert client.get(f"/api/v1{path}", headers=bearer(token)).status_code == 401


def test_other_account_cannot_update_or_delete_macros_and_applications(client):
    owner = bearer(create_account_and_token(client, "owner-release@example.com"))
    other = bearer(create_account_and_token(client, "other-release@example.com"))
    saved_macro = client.post(MACROS, headers=owner, json=macro()).json()
    saved_app = client.post(APPLICATIONS, headers=owner, json=application()).json()
    macro_url, app_url = f"{MACROS}/{saved_macro['id']}", f"{APPLICATIONS}/{saved_app['id']}"
    assert client.put(macro_url, headers=other, json=macro()).status_code == 404
    assert client.patch(macro_url, headers=other, json={"enabled": False}).status_code == 404
    assert client.delete(macro_url, headers=other).status_code == 404
    assert client.put(app_url, headers=other, json=application()).status_code == 404
    assert client.delete(app_url, headers=other).status_code == 404
    assert client.get(MACROS, headers=owner).json() == [saved_macro]
