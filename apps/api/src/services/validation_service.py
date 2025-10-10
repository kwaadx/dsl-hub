from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

from jsonschema import Draft7Validator
from typing import Any, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models import SchemaChannel, SchemaDef
from ..config import settings
import re

SEV_ERROR = {"required", "type", "enum"}

# cache of compiled validators
_VALIDATOR_CACHE: dict[str, Draft7Validator] = {}

def _validator_cache_key(channel: str, version: str | None, name: str | None) -> str:
    v = version or ""
    n = name or ""
    return f"{channel}:{v}:{n}"

class ValidationService:
    def __init__(self, db: Session):
        self.db = db

    def _active_schema(self) -> SchemaDef:
        ch = self.db.execute(select(SchemaChannel).where(SchemaChannel.name==settings.SCHEMA_CHANNEL)).scalar_one_or_none()
        if not ch:
            raise ValueError("No schema channel configured")
        schema_def = self.db.get(SchemaDef, ch.active_schema_def_id)
        return schema_def

    def validate_pipeline(self, pipeline: Dict[str, Any]) -> List[Dict[str, Any]]:
        schema_def = self._active_schema()
        schema = schema_def.json
        v = Draft7Validator(schema)
        issues: List[Dict[str, Any]] = []
        for e in v.iter_errors(pipeline):
            code = getattr(e, "validator", "schema") or "schema"
            # Build JSON Pointer-like path
            base_path = "/" + "/".join([str(x) for x in e.path])
            # For `required`, append the missing property to align with spec examples
            if code == "required":
                m = re.search(r"'([^']+)' is a required property", e.message)
                if m:
                    missing = m.group(1)
                    path = base_path + ("/" if base_path != "/" else "") + missing if base_path else "/" + missing
                else:
                    path = base_path or "/"
            else:
                path = base_path or "/"
            severity = "error" if code in SEV_ERROR else "warning"
            issues.append({
                "path": path,
                "code": code,
                "severity": severity,
                "message": e.message
            })
        # Domain rules: duplicate stage names (no exceptions needed)
        stages = pipeline.get("stages", []) if isinstance(pipeline, dict) else []
        if isinstance(stages, list):
            names = [s.get("name") for s in stages if isinstance(s, dict)]
            seen: dict[str, int] = {}
            for n in names:
                if n is None:
                    continue
                seen[n] = seen.get(n, 0) + 1
            for n, cnt in seen.items():
                if cnt > 1:
                    issues.append({
                        "path": "/stages",
                        "code": "duplicate_id",
                        "severity": "error",
                        "message": f"Duplicate stage name: {n}"
                    })
        return issues
