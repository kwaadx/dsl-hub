from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.testclient import TestClient

from ..middleware.idempotency import IdempotencyMiddleware
from ..middleware.error import AppError, handle_app_error


def build_app():
    app = FastAPI()
    app.add_middleware(IdempotencyMiddleware)
    app.add_exception_handler(AppError, handle_app_error)

    @app.post("/echo")
    async def echo(req: Request):
        data = await req.json()
        return JSONResponse({"ok": True, "data": data})

    return app


def test_idempotency_cache_hit():
    app = build_app()
    client = TestClient(app)

    headers = {"Idempotency-Key": "k1"}
    body = {"a": 1}

    r1 = client.post("/echo", json=body, headers=headers)
    assert r1.status_code == 200
    r2 = client.post("/echo", json=body, headers=headers)
    assert r2.status_code == 200
    assert r1.json() == r2.json()


def test_idempotency_conflict_different_body():
    app = build_app()
    client = TestClient(app)

    headers = {"Idempotency-Key": "k2"}
    r1 = client.post("/echo", json={"a": 1}, headers=headers)
    assert r1.status_code == 200
    r2 = client.post("/echo", json={"a": 2}, headers=headers)
    # Should be handled by AppError -> 409 with unified shape
    assert r2.status_code == 409
    data = r2.json()
    assert data.get("code") == "IDEMPOTENCY_KEY_REUSED"