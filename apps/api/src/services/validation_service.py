from jsonschema import Draft7Validator
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models import SchemaChannel, SchemaDef
from ..config import settings

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
            issues.append({
                "path": "/" + "/".join([str(x) for x in e.path]),
                "code": "schema_error",
                "severity": "error",
                "message": e.message
            })
        # TODO: add domain-specific rules here
        return issues
