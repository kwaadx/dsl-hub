from __future__ import annotations

from typing import Optional, Iterable
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models import Flow, Pipeline, ThreadSummary
from ..repositories import flow_repo as legacy_flow_repo
from ..repositories import pipeline_repo as legacy_pipeline_repo
from ..repositories import thread_summary_repo as legacy_ts_repo

class SAFlowRepo:
    def __init__(self, db: Session): self.db = db
    def get(self, flow_id: str) -> Optional[dict]:
        f = self.db.get(Flow, flow_id)
        if not f: return None
        return {"id": str(f.id), "slug": f.slug, "name": f.name}
    def get_by_slug(self, slug: str) -> Optional[dict]:
        q = self.db.execute(select(Flow).where(Flow.slug==slug)).scalar_one_or_none()
        if not q: return None
        return {"id": str(q.id), "slug": q.slug, "name": q.name}
    def create(self, name: str, slug: Optional[str]) -> dict:
        # reuse legacy behavior to keep invariants
        created = legacy_flow_repo.create(self.db, name=name, slug=slug)
        return {"id": str(created.id), "slug": created.slug, "name": created.name}
    def update(self, flow_id: str, *, name: Optional[str], slug: Optional[str]) -> dict:
        upd = legacy_flow_repo.update(self.db, flow_id, name=name, slug=slug)
        return {"id": str(upd.id), "slug": upd.slug, "name": upd.name}
    def delete(self, flow_id: str) -> bool:
        return legacy_flow_repo.delete(self.db, flow_id)
    def list(self, limit: int = 100, offset: int = 0) -> Iterable[dict]:
        rows = self.db.query(Flow).order_by(Flow.created_at.desc()).offset(offset).limit(limit).all()
        for f in rows:
            yield {"id": str(f.id), "slug": f.slug, "name": f.name}

class SAPipelineRepo:
    def __init__(self, db: Session): self.db = db
    def get(self, pipeline_id: str) -> Optional[dict]:
        p = self.db.get(Pipeline, pipeline_id)
        if not p: return None
        return {"id": str(p.id), "flow_id": p.flow_id, "json": p.json, "version": p.version}
    def create(self, flow_id: str, payload: dict) -> dict:
        created = legacy_pipeline_repo.create(self.db, flow_id, payload)
        return {"id": str(created.id), "flow_id": created.flow_id, "json": created.json, "version": created.version}
    def list_for_flow(self, flow_id: str, limit: int = 100, offset: int = 0) -> Iterable[dict]:
        rows = self.db.query(Pipeline).filter(Pipeline.flow_id==flow_id).order_by(Pipeline.created_at.desc()).offset(offset).limit(limit).all()
        for p in rows:
            yield {"id": str(p.id), "flow_id": p.flow_id, "json": p.json, "version": p.version}

class SAThreadSummaryRepo:
    def __init__(self, db: Session): self.db = db
    def list_for_thread(self, thread_id: str) -> Iterable[dict]:
        rows = legacy_ts_repo.list_for_thread(self.db, thread_id)
        for r in rows:
            yield legacy_ts_repo.payload(r)
    def create(self, thread_id: str, kind: str, content: dict, token_budget: int, covering_from, covering_to) -> dict:
        created = legacy_ts_repo.create(self.db, thread_id, kind=kind, content=content, token_budget=token_budget,
                                       covering_from=covering_from, covering_to=covering_to)
        return legacy_ts_repo.payload(created)

class SAFlowSummaryRepo:
    def __init__(self, db: Session): self.db = db
    def get_active(self, flow_id: str) -> dict | None:
        from ..repositories.flow_summary_repo import get_active, active_payload
        return active_payload(get_active(self.db, flow_id))
    def upsert_active(self, flow_id: str, *, content: dict, last_message_id: str | None) -> dict:
        from ..models import FlowSummary
        from sqlalchemy import select, update
        from sqlalchemy.orm import Session
        # Deactivate current
        cur = self.db.execute(select(FlowSummary).where(FlowSummary.flow_id==flow_id, FlowSummary.is_active==True)).scalar_one_or_none()  # noqa: E712
        if cur:
            cur.is_active = False
            self.db.add(cur)
        # New version
        import uuid
        version = (cur.version + 1) if cur else 1
        fs = FlowSummary(id=str(uuid.uuid4()), flow_id=flow_id, version=version, content=content, last_message_id=last_message_id, is_active=True)
        self.db.add(fs); self.db.flush(); self.db.refresh(fs)
        return {"version": fs.version, "content": fs.content, "last_message_id": str(fs.last_message_id) if fs.last_message_id else None}
