from fastapi import APIRouter, Depends, Body, Path, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from ..deps import db_session
from sqlalchemy.orm import Session
from ..models import SchemaUpgradePlan, PipelineUpgradeRun, Pipeline, SchemaDef

router = APIRouter(tags=["upgrades"])

class UpgradePlanCreate(BaseModel):
    from_schema_def_id: str
    to_schema_def_id: str
    strategy: str
    transform_spec: Optional[dict] = None

class UpgradePlanOut(BaseModel):
    id: str
    name: str
    from_schema_def_id: str
    to_schema_def_id: str
    strategy: str

@router.post("/schema/upgrade-plan", response_model=UpgradePlanOut, status_code=201)
def create_upgrade_plan(body: UpgradePlanCreate = Body(...), db: Session = Depends(db_session)) -> UpgradePlanOut:
    from_def = db.get(SchemaDef, body.from_schema_def_id)
    to_def = db.get(SchemaDef, body.to_schema_def_id)
    if not from_def or not to_def:
        raise HTTPException(status_code=400, detail="Invalid schema_def ids")
    # Validate strategy against allowed values to avoid DB CHECK violations
    allowed_strategies = {"transform", "no_change", "manual_only"}
    if body.strategy not in allowed_strategies:
        raise HTTPException(status_code=400, detail="Invalid strategy; expected one of: transform, no_change, manual_only")
    # Prevent from==to early (DB also enforces this)
    if str(body.from_schema_def_id) == str(body.to_schema_def_id):
        raise HTTPException(status_code=400, detail="from_schema_def_id must differ from to_schema_def_id")
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
    return UpgradePlanOut(
        id=str(plan.id),
        name=plan.name,
        from_schema_def_id=str(plan.from_schema_def_id),
        to_schema_def_id=str(plan.to_schema_def_id),
        strategy=plan.strategy,
    )

class UpgradeStart(BaseModel):
    upgrade_plan_id: str

class PipelineUpgradeRunOut(BaseModel):
    id: str
    pipeline_id: str
    status: str
    upgrade_plan_id: Optional[str] = None

@router.post("/pipelines/{pipeline_id}/upgrade", response_model=PipelineUpgradeRunOut, status_code=202)
def start_pipeline_upgrade(pipeline_id: str = Path(...), body: UpgradeStart = Body(...), db: Session = Depends(db_session)) -> PipelineUpgradeRunOut:
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
    return PipelineUpgradeRunOut(
        id=str(run.id),
        pipeline_id=str(run.pipeline_id),
        status=run.status,
        upgrade_plan_id=str(run.upgrade_plan_id) if run.upgrade_plan_id else None,
    )

@router.get("/pipeline-upgrade-runs")
def list_pipeline_upgrade_runs(pipeline_id: Optional[str] = None, db: Session = Depends(db_session)) -> List[Dict[str, Any]]:
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
