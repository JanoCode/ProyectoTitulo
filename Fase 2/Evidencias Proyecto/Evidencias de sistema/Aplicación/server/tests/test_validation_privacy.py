def test_validation_response_does_not_echo_passwords(client):
    password = "privado"
    response = client.post("/api/v1/auth/register", json={
        "name": "Usuario", "email": "incorrecto", "password": password,
    })
    assert response.status_code == 422
    assert password not in response.text
    assert '"input"' not in response.text
    assert response.json()["errors"]
