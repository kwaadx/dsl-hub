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
        t = Thread(id=thread_id, flow_id=flow_id, context_snapshot_id=snapshot_id)
        snap = ContextSnapshot(
            id=snapshot_id,
            flow_id=flow_id,
            origin_thread_id=thread_id,
            schema_def_id=schema_def_id,
            flow_summary_id=fs.id if fs else None,
            pipeline_id=pub.id if pub else None,
            notes={},
        )
        self.db.add_all([t, snap])
        self.db.flush()
        return t

    def get(self, thread_id: str) -> Optional[Thread]:
        return self.db.get(Thread, thread_id)
