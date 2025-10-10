from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

from sqlalchemy.orm import Session
from sqlalchemy import select, func
from ..models import Flow, Pipeline

class FlowRepo:
    def __init__(self, db: Session):
        self.db = db

    def list(self):
        published_count = self._published_count_subquery().label("published_count")
        active_version = self._active_version_subquery().label("active_version")
        stmt = select(Flow, published_count, active_version)
        return self.db.execute(stmt).all()

    def get_with_stats(self, flow_id: str):
        published_count = self._published_count_subquery().label("published_count")
        active_version = self._active_version_subquery().label("active_version")
        stmt = select(Flow, published_count, active_version).where(Flow.id == flow_id)
        return self.db.execute(stmt).one_or_none()

    @staticmethod
    def _published_count_subquery():
        return (
            select(func.count())
            .select_from(Pipeline)
            .where(Pipeline.flow_id == Flow.id, Pipeline.is_published == True)
            .scalar_subquery()
        )

    @staticmethod
    def _active_version_subquery():
        return (
            select(Pipeline.version)
            .where(Pipeline.flow_id == Flow.id, Pipeline.is_published == True)
            .order_by(Pipeline.created_at.desc())
            .limit(1)
            .scalar_subquery()
        )

    def create(self, flow_id, slug, name, meta=None):
        f = Flow(id=flow_id, slug=slug, name=name, meta=meta or {})
        self.db.add(f)
        self.db.flush()
        return f

    def get(self, flow_id):
        return self.db.get(Flow, flow_id)

    def update(self, flow_id: str, *, name: str | None = None, slug: str | None = None):
        f = self.get(flow_id)
        if f is None:
            return None
        if name is not None:
            f.name = name
        if slug is not None:
            f.slug = slug
        self.db.flush()
        return f

    def delete(self, flow_id: str) -> bool:
        f = self.get(flow_id)
        if f is None:
            return False
        self.db.delete(f)
        self.db.flush()
        # commit is handled by request lifecycle in get_db
        return True
