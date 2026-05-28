from fastapi.testclient import TestClient

from src.main import app


def test_health_endpoint_reports_runtime_readiness_shape() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert set(payload["runtime"]) == {"javaReady", "calibreReady", "epubcheckReady", "message"}


def test_health_endpoint_allows_local_web_origin() -> None:
    client = TestClient(app)

    response = client.get("/health", headers={"Origin": "http://127.0.0.1:3101"})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3101"
