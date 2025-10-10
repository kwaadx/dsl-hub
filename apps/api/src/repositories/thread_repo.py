from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models import Thread, ContextSnapshot, SchemaChannel, Pipeline
from ..config import settings
from ..repositories.flow_summary_repo import get_active as get_active_flow_summary
from ..middleware.error import AppError
import uuid

class ThreadRepo:
    def __init__(self, db: Session):
        self.db = db

    def create(self, thread_id: str, flow_id: str) -> Thread:
        # Ensure schema context is available before mutating session state
        channel = self.db.execute(
            select(SchemaChannel).where(SchemaChannel.name == settings.SCHEMA_CHANNEL)
        ).scalar_one_or_none()
        if channel is None:
            raise AppError(status=503, code="SCHEMA_CHANNEL_MISSING", message="No schema channel configured")
        schema_def_id = channel.active_schema_def_id
        if not schema_def_id:
            raise AppError(status=503, code="SCHEMA_DEFINITION_MISSING",
                           message="No active schema definition in the configured channel")

        fs = get_active_flow_summary(self.db, flow_id)
        pub = self.db.execute(
            select(Pipeline).where(Pipeline.flow_id == flow_id, Pipeline.is_published == True).limit(1)
        ).scalar_one_or_none()

        snapshot_id = str(uuid.uuid4())
        # Create ContextSnapshot first and flush to ensure it exists before inserting Thread
        snap = ContextSnapshot(
            id=snapshot_id,
            flow_id=flow_id,
            origin_thread_id=None,  # set after thread is created to avoid circular insert ordering
            schema_def_id=schema_def_id,
            flow_summary_id=fs.id if fs else None,
            pipeline_id=pub.id if pub else None,
            notes={},
        )
        self.db.add(snap)
        self.db.flush()  # guarantee snapshot row is persisted for trigger validation

        # Now create the thread that references the snapshot
        t = Thread(id=thread_id, flow_id=flow_id, context_snapshot_id=snapshot_id)
        self.db.add(t)
        self.db.flush()

        # Now that thread exists, backfill origin_thread_id for the snapshot
        snap.origin_thread_id = thread_id
        self.db.flush()
        return t

    def get(self, thread_id: str) -> Optional[Thread]:
        return self.db.get(Thread, thread_id)

    def list_for_flow(self, flow_id: str) -> list[Thread]:
        stmt = select(Thread).where(Thread.flow_id == flow_id).order_by(Thread.started_at.desc())
        return list(self.db.execute(stmt).scalars().all())
