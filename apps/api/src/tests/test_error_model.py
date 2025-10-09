from fastapi import FastAPI
from fastapi.testclient import TestClient

from ..middleware.error import AppError, handle_app_error, handle_http_error, handle_generic_error


def _make_app():
    app = FastAPI()
    app.add_exception_handler(AppError, handle_app_error)
    app.add_exception_handler(Exception, handle_generic_error)

    @app.get("/boom")
    def boom():  # type: ignore[unused-ignore]
        raise AppError(status=422, code="VALIDATION_FAILED", message="bad payload", details=[{"hint": "x"}])

    return app


def test_app_error_unified_shape():
    app = _make_app()
    client = TestClient(app)
    r = client.get("/boom")
    assert r.status_code == 422
    data = r.json()
    assert "error" in data
    err = data["error"]
    assert err["code"] == "VALIDATION_FAILED"
    assert err["message"] == "bad payload"
    assert isinstance(err.get("details"), list)
