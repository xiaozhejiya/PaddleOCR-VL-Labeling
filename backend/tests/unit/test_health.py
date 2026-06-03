from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_dependency_statuses() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"ok", "degraded"}
    assert payload["database"]["status"] in {"ok", "error", "not_configured"}
    assert payload["redis"]["status"] in {"ok", "error", "not_configured"}
