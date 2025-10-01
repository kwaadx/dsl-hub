# Minimal idempotent seed script: ensure one schema_def (v1.0.0) and a schema_channel('stable')
from src.database import SessionLocal, Base, engine
from src.models import SchemaDef, SchemaChannel
from sqlalchemy import select
import uuid

Base.metadata.create_all(engine)
db = SessionLocal()

schema = {
  "$schema":"http://json-schema.org/draft-07/schema#",
  "type":"object",
  "required":["name","stages"],
  "properties":{
    "name":{"type":"string"},
    "stages":{
      "type":"array",
      "items":{
        "type":"object",
        "required":["name","type","params"],
        "properties":{
          "name":{"type":"string"},
          "type":{"type":"string","enum":["source","map","reduce","sink"]},
          "params":{"type":"object"}
        }
      }
    }
  }
}

try:
    # upsert schema_def by name+version
    sdef = db.execute(select(SchemaDef).where(SchemaDef.name=="dsl-core", SchemaDef.version=="1.0.0")).scalar_one_or_none()
    if not sdef:
        sdef = SchemaDef(id=str(uuid.uuid4()), name="dsl-core", version="1.0.0", status="active", json=schema, compat_with=[])
        db.add(sdef); db.flush()
    # upsert channel 'stable'
    ch = db.execute(select(SchemaChannel).where(SchemaChannel.name=="stable")).scalar_one_or_none()
    if not ch:
        ch = SchemaChannel(id=str(uuid.uuid4()), name="stable", active_schema_def_id=sdef.id)
        db.add(ch); db.flush()
    else:
        ch.active_schema_def_id = sdef.id
        db.flush()
    db.commit()
    print("Seed OK")
finally:
    db.close()
