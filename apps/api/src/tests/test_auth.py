from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from ..middleware.auth import AuthMiddleware
from ..config import settings


def _make_app():
    app = FastAPI()
    app.add_middleware(AuthMiddleware)

    @app.post("/ok")
    def ok():  # type: ignore[unused-ignore]
        return JSONResponse({"ok": True})

    return app


def test_auth_unauthorized_when_token_set_and_missing_header(monkeypatch):
    # Ensure token is set for the scope of this test
    monkeypatch.setattr(settings, "AUTH_TOKEN", "secret-token", raising=False)
    app = _make_app()
    client = TestClient(app)
    r = client.post("/ok")
    assert r.status_code == 401
    data = r.json()
    assert data.get("error", {}).get("code") == "UNAUTHORIZED"


def test_auth_ok_with_bearer_token(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_TOKEN", "secret-token", raising=False)
    app = _make_app()
    client = TestClient(app)
    r = client.post("/ok", headers={"Authorization": "Bearer secret-token"})
    assert r.status_code == 200
    assert r.json() == {"ok": True}
