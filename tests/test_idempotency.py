from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from apps.api.src.middleware.idempotency import IdempotencyMiddleware


def _make_app():
    app = FastAPI()
    app.add_middleware(IdempotencyMiddleware)

    @app.post("/echo")
    async def echo(req: Request):  # type: ignore[unused-ignore]
        data = await req.json()
        return JSONResponse(data)

    return app


def test_idempotency_caches_same_key_and_body():
    app = _make_app()
    client = TestClient(app)
    headers = {"Idempotency-Key": "abc-123"}
    payload = {"x": 1}
    r1 = client.post("/echo", json=payload, headers=headers)
    assert r1.status_code == 200
    r2 = client.post("/echo", json=payload, headers=headers)
    assert r2.status_code == 200
    assert r2.json() == payload


def test_idempotency_conflict_on_different_body():
    app = _make_app()
    client = TestClient(app)
    headers = {"Idempotency-Key": "key-1"}
    r1 = client.post("/echo", json={"a": 1}, headers=headers)
    assert r1.status_code == 200
    r2 = client.post("/echo", json={"a": 2}, headers=headers)
    assert r2.status_code == 409
    data = r2.json()
    assert data.get("error", {}).get("code") == "IDEMPOTENCY_KEY_REUSED"