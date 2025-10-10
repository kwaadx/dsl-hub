from __future__ import annotations

from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from ..deps import compat_repo
from ..models import CompatRule
from sqlalchemy.orm import Session
from ..deps import db_session

router = APIRouter(prefix="/admin/compat", tags=["admin"])

@router.get("/{subject_kind}/{subject_key}/{subject_version}")
def list_rules(subject_kind: str, subject_key: str, subject_version: str, repo = Depends(compat_repo)) -> List[Dict[str, Any]]:
    return list(repo.list_for_subject(subject_kind, subject_key, subject_version))

class CompatCreateIn(BaseModel):
    subject_kind: str
    subject_key: str
    subject_version: str
    requires_kind: str
    requires_key: str
    requires_version: str
    rule: Dict[str, Any]

@router.post("")
def create_rule(body: CompatCreateIn, db: Session = Depends(db_session)) -> Dict[str, Any]:
    from uuid import uuid4
    row = CompatRule(
        id=str(uuid4()),
        subject_kind=body.subject_kind,
        subject_key=body.subject_key,
        subject_version=body.subject_version,
        requires_kind=body.requires_kind,
        requires_key=body.requires_key,
        requires_version=body.requires_version,
        rule=body.rule
    )
    db.add(row); db.flush(); db.refresh(row)
    return {"id": str(row.id)}