from fastapi.testclient import TestClient

from src.main import app


def test_health_endpoint_reports_runtime_readiness_shape() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert set(payload["runtime"]) == {"javaReady", "calibreReady", "epubcheckReady", "message"}
