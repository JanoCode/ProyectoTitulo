from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_cp_02_19_health_responde_ok():
    """Prueba que la ruta /health responde con un estado 200 y un mensaje de estado 'ok'."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}