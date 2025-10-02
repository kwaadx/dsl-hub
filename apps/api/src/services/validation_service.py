from jsonschema import Draft7Validator
from typing import Any, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models import SchemaChannel, SchemaDef
from ..config import settings

SEV_ERROR = {"required", "type", "enum"}

class ValidationService:
    def __init__(self, db: Session):
        self.db = db

    def _active_schema(self) -> SchemaDef:
        ch = self.db.execute(select(SchemaChannel).where(SchemaChannel.name==settings.APP_SCHEMA_CHANNEL)).scalar_one_or_none()
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
            path = "/" + "/".join([str(x) for x in e.path])
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
