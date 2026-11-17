import pytest

from tests.test_settings import bearer, create_account_and_token


def test_side_is_saved_and_returned_on_the_next_login(client):
    token = create_account_and_token(client, "side@example.com")
    headers = bearer(token)
    assert client.get("/api/v1/settings", headers=headers).json()["gesture_control_side"] == "right"
    changed = client.patch("/api/v1/settings", headers=headers,
                           json={"gesture_control_side": "left"})
    assert changed.status_code == 200
    assert changed.json()["gesture_control_side"] == "left"
    assert client.get("/api/v1/settings", headers=headers).json()["gesture_control_side"] == "left"


@pytest.mark.parametrize("value", ["center", "", None, 1, True])
def test_unknown_side_does_not_replace_saved_preference(client, value):
    headers = bearer(create_account_and_token(client, "invalid-side@example.com"))
    assert client.patch("/api/v1/settings", headers=headers,
                        json={"gesture_control_side": value}).status_code == 422
    assert client.get("/api/v1/settings", headers=headers).json()["gesture_control_side"] == "right"
