from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models import SchemaChannel, SchemaDef

class SASchemaRepo:
    def __init__(self, db: Session): self.db = db
    def get_active_schema(self, channel: str):
        row = self.db.execute(select(SchemaChannel).where(SchemaChannel.name==channel)).scalar_one_or_none()
        if not row or not row.active_schema_def_id:
            return None
        d = self.db.get(SchemaDef, row.active_schema_def_id)
        if not d:
            return None
        return {"id": str(d.id), "name": d.name, "version": d.version, "json": d.json}