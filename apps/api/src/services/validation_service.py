from jsonschema import Draft7Validator
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models import SchemaChannel, SchemaDef
from ..config import settings

SEV_ERROR = {"required", "type", "enum"}

class ValidationService:
    def __init__(self, db: Session):
        self.db = db

    def _active_schema(self):
        ch = self.db.execute(select(SchemaChannel).where(SchemaChannel.name==settings.APP_SCHEMA_CHANNEL)).scalar_one_or_none()
        if not ch:
            raise ValueError("No schema channel configured")
        sdef = self.db.get(SchemaDef, ch.active_schema_def_id)
        return sdef

    def validate_pipeline(self, pipeline: dict):
        sdef = self._active_schema()
        schema = sdef.json
        v = Draft7Validator(schema)
        issues = []
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
        # Domain rules: duplicate stage names
        try:
            stages = pipeline.get("stages", []) if isinstance(pipeline, dict) else []
            names = [s.get("name") for s in stages if isinstance(s, dict)]
            dups = {n for n in names if n is not None and names.count(n) > 1}
            for n in dups:
                issues.append({
                    "path": "/stages",
                    "code": "duplicate_id",
                    "severity": "error",
                    "message": f"Duplicate stage name: {n}"
                })
        except Exception:
            pass
        return issues
