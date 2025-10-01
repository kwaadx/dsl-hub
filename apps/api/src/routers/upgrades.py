from fastapi import APIRouter, Depends, Body, Path, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..database import get_db
from ..models import SchemaUpgradePlan, PipelineUpgradeRun, Pipeline, SchemaDef

router = APIRouter(tags=["upgrades"])

class UpgradePlanCreate(BaseModel):
    from_schema_def_id: str
    to_schema_def_id: str
    strategy: str
    transform_spec: Optional[dict] = None

@router.post("/schema/upgrade-plan")
def create_upgrade_plan(body: UpgradePlanCreate = Body(...), db: Session = Depends(get_db)):
    from_def = db.get(SchemaDef, body.from_schema_def_id)
    to_def = db.get(SchemaDef, body.to_schema_def_id)
    if not from_def or not to_def:
        raise HTTPException(status_code=400, detail="Invalid schema_def ids")
    import uuid
    plan = SchemaUpgradePlan(
        id=str(uuid.uuid4()),
        name=f"{body.strategy}-plan",
        from_schema_def_id=body.from_schema_def_id,
        to_schema_def_id=body.to_schema_def_id,
        strategy=body.strategy,
        transform_spec=body.transform_spec or {},
    )
    db.add(plan); db.flush()
    return {
        "id": str(plan.id),
        "name": plan.name,
        "from_schema_def_id": str(plan.from_schema_def_id),
        "to_schema_def_id": str(plan.to_schema_def_id),
        "strategy": plan.strategy,
    }

class UpgradeStart(BaseModel):
    upgrade_plan_id: str

@router.post("/pipelines/{pipeline_id}/upgrade")
def start_pipeline_upgrade(pipeline_id: str = Path(...), body: UpgradeStart = Body(...), db: Session = Depends(get_db)):
    p = db.get(Pipeline, pipeline_id)
    if not p:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    plan = db.get(SchemaUpgradePlan, body.upgrade_plan_id)
    if not plan:
        raise HTTPException(status_code=400, detail="Invalid upgrade_plan_id")
    import uuid
    run = PipelineUpgradeRun(
        id=str(uuid.uuid4()),
        pipeline_id=pipeline_id,
        from_schema_def_id=p.schema_def_id,
        to_schema_def_id=plan.to_schema_def_id,
        upgrade_plan_id=body.upgrade_plan_id,
        status="queued",
        mode="auto",
    )
    db.add(run); db.flush()
    return {
        "id": str(run.id),
        "pipeline_id": str(run.pipeline_id),
        "status": run.status,
        "upgrade_plan_id": str(run.upgrade_plan_id) if run.upgrade_plan_id else None,
    }

@router.get("/pipeline-upgrade-runs")
def list_pipeline_upgrade_runs(pipeline_id: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(PipelineUpgradeRun)
    if pipeline_id:
        q = q.filter(PipelineUpgradeRun.pipeline_id == pipeline_id)
    rows = q.order_by(PipelineUpgradeRun.created_at.desc()).all()
    return [{
        "id": str(r.id),
        "pipeline_id": str(r.pipeline_id),
        "from_schema_def_id": str(r.from_schema_def_id),
        "to_schema_def_id": str(r.to_schema_def_id),
        "upgrade_plan_id": str(r.upgrade_plan_id) if r.upgrade_plan_id else None,
        "status": r.status,
        "mode": r.mode,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "finished_at": r.finished_at.isoformat() if r.finished_at else None,
    } for r in rows]
