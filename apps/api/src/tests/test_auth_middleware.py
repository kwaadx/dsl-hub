from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.testclient import TestClient

from ..middleware.auth import AuthMiddleware
from ..middleware.error import AppError, handle_app_error
from ..config import settings


def build_app():
    app = FastAPI()
    app.add_middleware(AuthMiddleware)
    app.add_exception_handler(AppError, handle_app_error)

    @app.post("/ok")
    async def ok():
        return JSONResponse({"ok": True})

    return app


def test_auth_requires_token_when_enabled(monkeypatch):
    # Enable token auth
    monkeypatch.setattr(settings, "AUTH_TOKEN", "secret")
    app = build_app()
    client = TestClient(app)

    # No header -> 401
    r = client.post("/ok")
    assert r.status_code == 401
    assert r.json().get("code") == "UNAUTHORIZED"

    # Correct header -> 200
    r2 = client.post("/ok", headers={"Authorization": "Bearer secret"})
    assert r2.status_code == 200
    assert r2.json().get("ok") is True


def test_auth_no_enforcement_when_disabled(monkeypatch):
    # Disable auth
    monkeypatch.setattr(settings, "AUTH_TOKEN", None)
    app = build_app()
    client = TestClient(app)

    # Should pass without header
    r = client.post("/ok")
    assert r.status_code == 200
    assert r.json().get("ok") is True
