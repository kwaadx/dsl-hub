from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models import Thread, ContextSnapshot, SchemaChannel, Pipeline
from ..config import settings
from ..repositories.flow_summary_repo import get_active as get_active_flow_summary
import uuid

class ThreadRepo:
    def __init__(self, db: Session):
        self.db = db

    def create(self, thread_id: str, flow_id: str) -> Thread:
        t = Thread(id=thread_id, flow_id=flow_id)
        self.db.add(t); self.db.flush()
        # Context snapshot from active artifacts
        channel = self.db.execute(select(SchemaChannel).where(SchemaChannel.name==settings.APP_SCHEMA_CHANNEL)).scalar_one_or_none()
        schema_def_id = channel.active_schema_def_id if channel else None
        if not schema_def_id:
            raise ValueError("No schema channel configured")

        fs = get_active_flow_summary(self.db, flow_id)
        pub = self.db.execute(select(Pipeline).where(Pipeline.flow_id==flow_id, Pipeline.is_published==True).limit(1)).scalar_one_or_none()

        snap = ContextSnapshot(id=str(uuid.uuid4()),
                               flow_id=flow_id,
                               origin_thread_id=t.id,
                               schema_def_id=schema_def_id,
                               flow_summary_id=fs.id if fs else None,
                               pipeline_id=pub.id if pub else None,
                               notes={})
        self.db.add(snap); self.db.flush()
        t.context_snapshot_id = snap.id
        self.db.flush()
        return t

    def get(self, thread_id: str) -> Optional[Thread]:
        return self.db.get(Thread, thread_id)
