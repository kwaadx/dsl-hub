from types import SimpleNamespace

from apps.api.src.services.validation_service import ValidationService


class DummyDB:
    """A minimal placeholder; we will monkeypatch _active_schema and not use DB."""
    pass


def test_validation_required_path_formatting(monkeypatch):
    svc = ValidationService(DummyDB())
    # Monkeypatch _active_schema to return object with .json property (schema)
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["name", "stages"],
        "properties": {
            "name": {"type": "string"},
            "stages": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["name", "type", "params"],
                    "properties": {
                        "name": {"type": "string"},
                        "type": {"type": "string", "enum": ["source", "map", "reduce", "sink"]},
                        "params": {"type": "object"},
                    },
                },
            },
        },
    }
    dummy = SimpleNamespace(json=schema)
    monkeypatch.setattr(ValidationService, "_active_schema", lambda self: dummy, raising=False)

    # Missing stages[0].name -> path should be /stages/0/name
    pipeline = {
        "name": "p",
        "stages": [
            {"type": "source", "params": {}},
        ],
    }
    issues = svc.validate_pipeline(pipeline)
    paths = [it["path"] for it in issues]
    assert "/stages/0/name" in paths
    # Ensure severity mapping marks required as error
    for it in issues:
        if it["path"] == "/stages/0/name":
            assert it["code"] == "required"
            assert it["severity"] == "error"
            break
    else:
        raise AssertionError("Required issue for /stages/0/name not found")
