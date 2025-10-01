# Minimal seed script: insert one schema_def (v1.0.0) and a schema_channel('stable')
from src.database import SessionLocal, Base, engine
from src.models import SchemaDef, SchemaChannel
import uuid, json

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

sid = str(uuid.uuid4())
sdef = SchemaDef(id=sid, name="dsl-core", version="1.0.0", status="active", json=schema, compat_with=[])
db.add(sdef); db.flush()

ch = SchemaChannel(id=str(uuid.uuid4()), name="stable", active_schema_def_id=sid)
db.add(ch); db.flush()
db.commit()
print("Seed OK")
