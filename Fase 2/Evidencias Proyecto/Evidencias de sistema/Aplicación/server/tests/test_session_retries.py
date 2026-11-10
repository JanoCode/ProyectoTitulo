from tests.test_usage_sessions import bearer, create_account_and_token


def test_repeated_session_creation_preserves_the_server_reference(client, database):
    from app.models import UsageSession

    headers = bearer(create_account_and_token(client, "retry@example.com"))
    data = {"started_at": "2026-11-10T12:00:00Z"}
    first = client.post("/api/v1/usage-sessions", headers=headers, json=data)
    repeated = client.post("/api/v1/usage-sessions", headers=headers, json=data)
    assert repeated.status_code == 201
    assert first.json()["id"] == repeated.json()["id"]
    assert database.query(UsageSession).count() == 1
