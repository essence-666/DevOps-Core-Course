from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_health_success():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert isinstance(data["uptime_seconds"], int)
