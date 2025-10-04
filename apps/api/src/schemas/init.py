# Minimal idempotent init script: ensure one schema_def (v1.0.0) and a schema_channel('stable')
from ..database import SessionLocal, Base, engine
from ..models import SchemaDef, SchemaChannel
from ..config import settings
from sqlalchemy import select
import uuid
import json


# Fallback minimal schema in case the file is missing/unreadable
_fallback_schema = {
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
          "params": {"type": "object"}
        }
      }
    }
  }
}


def main() -> None:
    """Idempotent initialization routine used on container start.
    - Reads schema JSON from settings.INIT_SCHEMA_PATH if provided, otherwise 'v1.0.0.json'.
    - Ensures schema_def(name='dsl-core', version='1.0.0') exists/updated.
    - Ensures schema_channel('stable') points to that schema.
    """
    Base.metadata.create_all(engine)
    db = SessionLocal()

    schema_path = settings.INIT_SCHEMA_PATH or "v1.0.0.json"

    try:
        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                schema = json.load(f)
        except Exception as e:
            print(f"Warning: failed to load schema from {schema_path}: {e}. Using fallback schema.")
            schema = _fallback_schema

        # upsert schema_def by name+version
        sdef = db.execute(
            select(SchemaDef).where(SchemaDef.name == "dsl-core", SchemaDef.version == "1.0.0")
        ).scalar_one_or_none()
        if not sdef:
            sdef = SchemaDef(
                id=str(uuid.uuid4()),
                name="dsl-core",
                version="1.0.0",
                status="active",
                json=schema,
                compat_with=[],
            )
            db.add(sdef)
            db.flush()
        else:
            # Keep the same id/version but refresh JSON with the latest loaded schema
            sdef.json = schema
            db.flush()

        # upsert channel 'stable'
        ch = db.execute(select(SchemaChannel).where(SchemaChannel.name == "stable")).scalar_one_or_none()
        if not ch:
            ch = SchemaChannel(id=str(uuid.uuid4()), name="stable", active_schema_def_id=sdef.id)
            db.add(ch)
            db.flush()
        else:
            ch.active_schema_def_id = sdef.id
            db.flush()

        db.commit()
        print("Init OK")
    finally:
        db.close()


if __name__ == "__main__":
    main()
