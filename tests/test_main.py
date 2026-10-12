from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_openapi_and_docs_available():
    docs_resp = client.get("/docs")
    assert docs_resp.status_code == 200

    openapi_resp = client.get("/openapi.json")
    assert openapi_resp.status_code == 200
    assert "paths" in openapi_resp.json()

def test_api_routes_not_intercepted_by_spa():
    # An invalid API route must return a 404 status, NOT HTML or 200
    response = client.get("/api/v1/invalid-route")
    assert response.status_code == 404
    assert response.headers.get("content-type", "").startswith("application/json")

def test_spa_serving_and_fallback(tmp_path, monkeypatch):
    import os
    frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
    if os.path.isdir(frontend_dist) and os.path.isfile(os.path.join(frontend_dist, "index.html")):
        # When frontend/dist is built:
        root_resp = client.get("/")
        assert root_resp.status_code == 200
        assert "text/html" in root_resp.headers.get("content-type", "")

        spa_resp = client.get("/some-client-route")
        assert spa_resp.status_code == 200
        assert "text/html" in spa_resp.headers.get("content-type", "")
