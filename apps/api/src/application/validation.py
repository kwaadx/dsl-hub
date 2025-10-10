from __future__ import annotations

from ..app_decorators import instrument_uc
from typing import Any, Dict, List
from jsonschema import Draft7Validator
from ..core.ports import SchemaRepo
from ..core.errors import ValidationFailed

_CACHE: dict[str, Draft7Validator] = {}

def _key(channel: str, version: str | None) -> str:
    return f"{channel}:{version or ''}"

class ValidatePayload:
    @instrument_uc('ValidatePayload')
    def __init__(self, schemas: SchemaRepo):
        self.schemas = schemas
    def __call__(self, channel: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        schema = self.schemas.get_active_schema(channel)
        if not schema:
            raise ValidationFailed(f"No active schema in channel={channel}")
        version = schema.get("version")
        k = _key(channel, version)
        v = _CACHE.get(k)
        if v is None:
            v = Draft7Validator(schema["json"] if "json" in schema else schema)
            _CACHE[k] = v
        errors = []
        for e in v.iter_errors(payload):
            path = list(e.path)
            sev = "ERROR" if e.validator in {"required", "type", "enum"} else "WARN"
            errors.append({"path": path, "message": e.message, "severity": sev})
        return {"ok": not any(e["severity"]=="ERROR" for e in errors), "errors": errors, "schema_version": version}