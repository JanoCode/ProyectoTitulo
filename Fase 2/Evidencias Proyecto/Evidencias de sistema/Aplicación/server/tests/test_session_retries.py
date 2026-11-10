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


def test_repeated_break_creation_does_not_lose_following_events(client, database):
    from app.models import Break

    headers = bearer(create_account_and_token(client, "break-retry@example.com"))
    session = client.post("/api/v1/usage-sessions", headers=headers,
                          json={"started_at": "2026-11-10T12:00:00Z"}).json()
    url = f"/api/v1/usage-sessions/{session['id']}/breaks"
    data = {"started_at": "2026-11-10T12:10:00Z"}
    first = client.post(url, headers=headers, json=data).json()
    repeated = client.post(url, headers=headers, json=data)
    assert repeated.status_code == 201
    assert repeated.json()["id"] == first["id"]
    assert database.query(Break).count() == 1
    closed = client.patch(f"/api/v1/breaks/{first['id']}", headers=headers,
                          json={"ended_at": "2026-11-10T12:15:00Z"})
    assert closed.status_code == 200
