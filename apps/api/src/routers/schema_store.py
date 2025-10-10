from __future__ import annotations

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from ..schemas import registry
from ..deps import validation_service_port

router = APIRouter(prefix="/schemas/store", tags=["schemas"])

@router.get("")
def list_fs_packages() -> List[Dict[str, Any]]:
    return registry.list_packages()

@router.get("/{key}/{version}")
def get_fs_package(key: str, version: str) -> Dict[str, Any]:
    pkg = registry.get_package(key, version)
    if not pkg:
        raise HTTPException(404, "Schema package not found")
    return pkg

class ImportSchemaIn(BaseModel):
    activate: bool = True

@router.post("/{key}/{version}/import")
def import_schema(key: str, version: str, body: ImportSchemaIn, vs = Depends(validation_service_port)) -> Dict[str, Any]:
    pkg = registry.get_package(key, version)
    if not pkg: raise HTTPException(404, "Schema package not found")
    meta, schema = pkg["meta"], pkg["schema"]
    # save via validation service (expects repo inside). We assume it has "upsert_schema(key, version, schema, active=True/False)"
    try:
        out = vs.schemas.upsert_schema(channel=meta["key"], version=meta["version"], schema=schema, is_active=body.activate)
    except AttributeError:
        # fallback: return schema for manual import
        return {"status":"preview_only","schema": schema, "meta": meta}
    return {"status":"imported","meta": meta, "result": out}