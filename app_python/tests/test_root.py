from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_root_success():
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    # service block
    assert "service" in data
    assert data["service"]["name"] == "devops-info-service"
    assert data["service"]["version"] == "1.0.0"
    assert data["service"]["framework"] == "FastAPI"

    # system block
    assert "system" in data
    assert "hostname" in data["system"]
    assert "cpu_count" in data["system"]

    # runtime block
    assert "runtime" in data
    assert "uptime_seconds" in data["runtime"]
    assert isinstance(data["runtime"]["uptime_seconds"], int)

    # request block
    assert data["request"]["method"] == "GET"
    assert data["request"]["path"] == "/"

    # endpoints list
    assert isinstance(data["endpoints"], list)
    assert any(e["path"] == "/health" for e in data["endpoints"])
