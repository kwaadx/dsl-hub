from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models import Thread, ContextSnapshot, SchemaChannel, FlowSummary, Pipeline, SchemaDef
from ..config import settings

class ThreadRepo:
    def __init__(self, db: Session):
        self.db = db

    def create(self, id, flow_id):
        t = Thread(id=id, flow_id=flow_id)
        self.db.add(t); self.db.flush()
        # Context snapshot from active artifacts
        channel = self.db.execute(select(SchemaChannel).where(SchemaChannel.name==settings.APP_SCHEMA_CHANNEL)).scalar_one_or_none()
        schema_def_id = channel.active_schema_def_id if channel else None

        fs = self.db.execute(select(FlowSummary).where(FlowSummary.flow_id==flow_id, FlowSummary.is_active==True).limit(1)).scalar_one_or_none()
        pub = self.db.execute(select(Pipeline).where(Pipeline.flow_id==flow_id, Pipeline.is_published==True).limit(1)).scalar_one_or_none()

        snap = ContextSnapshot(id=id.replace('-', '')[:32] + "snap",  # naive id for demo
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

    def get(self, thread_id):
        return self.db.get(Thread, thread_id)
