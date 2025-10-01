from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey, JSON, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ARRAY
import enum
from .database import Base

# Enums used in code logic only (DB stores text)
class ThreadStatus(str, enum.Enum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"

# Models aligned with SQL schema (singular table names)
class Flow(Base):
    __tablename__ = "flow"

    id = Column(UUID(as_uuid=False), primary_key=True, index=True)
    slug = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    meta = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relations
    threads = relationship("Thread", back_populates="flow", cascade="all, delete-orphan")
    pipelines = relationship("Pipeline", back_populates="flow")
    summaries = relationship("FlowSummary", back_populates="flow")
    logs = relationship("AgentLog", back_populates="flow")
    generation_runs = relationship("GenerationRun", back_populates="flow")
    summary_runs = relationship("SummaryRun", back_populates="flow")

class Thread(Base):
    __tablename__ = "thread"

    id = Column(UUID(as_uuid=False), primary_key=True, index=True)
    flow_id = Column(UUID(as_uuid=False), ForeignKey("flow.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, nullable=False, default=ThreadStatus.NEW.value)
    result_pipeline_id = Column(UUID(as_uuid=False), ForeignKey("pipeline.id", ondelete="SET NULL"), nullable=True)
    context_snapshot_id = Column(UUID(as_uuid=False), ForeignKey("context_snapshot.id", ondelete="SET NULL"), nullable=True)
    archived = Column(Boolean, nullable=False, default=False)
    archived_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, server_default=func.now(), nullable=False)
    closed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relations
    flow = relationship("Flow", back_populates="threads")
    messages = relationship("Message", back_populates="thread", cascade="all, delete-orphan")
    logs = relationship("AgentLog", back_populates="thread")
    result_pipeline = relationship("Pipeline", foreign_keys=[result_pipeline_id])
    context_snapshot = relationship("ContextSnapshot", foreign_keys=[context_snapshot_id])
    thread_summaries = relationship("ThreadSummary", back_populates="thread")
    generation_runs = relationship("GenerationRun", back_populates="thread")
    summary_runs = relationship("SummaryRun", back_populates="thread")

class Message(Base):
    __tablename__ = "message"

    id = Column(UUID(as_uuid=False), primary_key=True, index=True)
    thread_id = Column(UUID(as_uuid=False), ForeignKey("thread.id", ondelete="CASCADE"), nullable=False)
    role = Column(String, nullable=False)  # user|assistant|system|tool
    format = Column(String, nullable=False, default="text")  # text|markdown|json|buttons|card
    parent_id = Column(UUID(as_uuid=False), ForeignKey("message.id", ondelete="SET NULL"), nullable=True)
    tool_name = Column(String, nullable=True)
    tool_result = Column(JSON, nullable=True)
    content = Column(JSON, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relations
    thread = relationship("Thread", back_populates="messages")
    parent = relationship("Message", remote_side=[id], uselist=False)

class SchemaDef(Base):
    __tablename__ = "schema_def"

    id = Column(UUID(as_uuid=False), primary_key=True, index=True)
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    status = Column(String, nullable=False, default="active")
    json = Column(JSON, nullable=False)
    compat_with = Column(ARRAY(String), nullable=False, default=list)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relations
    pipelines = relationship("Pipeline", back_populates="schema_def")
    schema_channels = relationship("SchemaChannel", back_populates="active_schema")
    context_snapshots = relationship("ContextSnapshot", back_populates="schema_def")
    upgrade_plans_from = relationship("SchemaUpgradePlan", back_populates="from_schema_def", foreign_keys=lambda: [SchemaUpgradePlan.from_schema_def_id])
    upgrade_plans_to = relationship("SchemaUpgradePlan", back_populates="to_schema_def", foreign_keys=lambda: [SchemaUpgradePlan.to_schema_def_id])
    compat_rules = relationship("CompatRule", back_populates="schema_def")

class SchemaChannel(Base):
    __tablename__ = "schema_channel"

    id = Column(UUID(as_uuid=False), primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    active_schema_def_id = Column(UUID(as_uuid=False), ForeignKey("schema_def.id", ondelete="RESTRICT"), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relations
    active_schema = relationship("SchemaDef", back_populates="schema_channels")

class Pipeline(Base):
    __tablename__ = "pipeline"

    id = Column(UUID(as_uuid=False), primary_key=True, index=True)
    flow_id = Column(UUID(as_uuid=False), ForeignKey("flow.id", ondelete="CASCADE"), nullable=False)
    version = Column(String, nullable=False)
    schema_version = Column(String, nullable=False)
    schema_def_id = Column(UUID(as_uuid=False), ForeignKey("schema_def.id", ondelete="RESTRICT"), nullable=True)
    status = Column(String, nullable=False, default="draft")
    is_published = Column(Boolean, nullable=False, default=False)
    content = Column(JSON, nullable=False)
    content_hash = Column(LargeBinary, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relations
    flow = relationship("Flow", back_populates="pipelines")
    schema_def = relationship("SchemaDef", back_populates="pipelines")
    generation_runs = relationship("GenerationRun", back_populates="pipeline")

class GenerationRun(Base):
    __tablename__ = "generation_run"

    id = Column(UUID(as_uuid=False), primary_key=True, index=True)
    flow_id = Column(UUID(as_uuid=False), ForeignKey("flow.id", ondelete="CASCADE"), nullable=False)
    thread_id = Column(UUID(as_uuid=False), ForeignKey("thread.id", ondelete="SET NULL"), nullable=True)
    pipeline_id = Column(UUID(as_uuid=False), ForeignKey("pipeline.id", ondelete="SET NULL"), nullable=True)
    stage = Column(String, nullable=False)  # discovery|generate|self_check|hard_validate|publish
    status = Column(String, nullable=False, default="queued")  # queued|running|succeeded|failed|canceled
    source = Column(JSON, nullable=False)
    result = Column(JSON, nullable=True)
    error = Column(String, nullable=True)
    cost = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    # Relations
    flow = relationship("Flow", back_populates="generation_runs")
    thread = relationship("Thread", back_populates="generation_runs")
    pipeline = relationship("Pipeline", back_populates="generation_runs")
    validation_issues = relationship("ValidationIssue", back_populates="generation_run", cascade="all, delete-orphan")

class ValidationIssue(Base):
    __tablename__ = "validation_issue"

    id = Column(UUID(as_uuid=False), primary_key=True, index=True)
    generation_run_id = Column(UUID(as_uuid=False), ForeignKey("generation_run.id", ondelete="CASCADE"), nullable=False)
    path = Column(String, nullable=False)
    code = Column(String, nullable=False)
    severity = Column(String, nullable=False)  # info|warning|error
    message = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relations
    generation_run = relationship("GenerationRun", back_populates="validation_issues")

class FlowSummary(Base):
    __tablename__ = "flow_summary"

    id = Column(UUID(as_uuid=False), primary_key=True, index=True)
    flow_id = Column(UUID(as_uuid=False), ForeignKey("flow.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    content = Column(JSON, nullable=False)
    pinned = Column(JSON, nullable=False, default=dict)
    last_message_id = Column(UUID(as_uuid=False), ForeignKey("message.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relations
    flow = relationship("Flow", back_populates="summaries")
    last_message = relationship("Message", foreign_keys=[last_message_id])
    summary_runs = relationship("SummaryRun", back_populates="flow_summary")
    context_snapshots = relationship("ContextSnapshot", back_populates="flow_summary")

class ThreadSummary(Base):
    __tablename__ = "thread_summary"

    id = Column(UUID(as_uuid=False), primary_key=True, index=True)
    thread_id = Column(UUID(as_uuid=False), ForeignKey("thread.id", ondelete="CASCADE"), nullable=False)
    kind = Column(String, nullable=False, default="short")  # short|detailed|system
    content = Column(JSON, nullable=False)
    token_budget = Column(Integer, nullable=False, default=1024)
    covering_from = Column(DateTime, nullable=True)
    covering_to = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relations
    thread = relationship("Thread", back_populates="thread_summaries")

class ContextSnapshot(Base):
    __tablename__ = "context_snapshot"

    id = Column(UUID(as_uuid=False), primary_key=True, index=True)
    flow_id = Column(UUID(as_uuid=False), ForeignKey("flow.id", ondelete="CASCADE"), nullable=False)
    origin_thread_id = Column(UUID(as_uuid=False), ForeignKey("thread.id", ondelete="SET NULL"), nullable=True)
    schema_def_id = Column(UUID(as_uuid=False), ForeignKey("schema_def.id", ondelete="RESTRICT"), nullable=False)
    flow_summary_id = Column(UUID(as_uuid=False), ForeignKey("flow_summary.id", ondelete="SET NULL"), nullable=True)
    pipeline_id = Column(UUID(as_uuid=False), ForeignKey("pipeline.id", ondelete="SET NULL"), nullable=True)
    notes = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relations
    flow = relationship("Flow")
    origin_thread = relationship("Thread", foreign_keys=[origin_thread_id])
    schema_def = relationship("SchemaDef", back_populates="context_snapshots")
    flow_summary = relationship("FlowSummary", back_populates="context_snapshots")
    pipeline = relationship("Pipeline")

class SummaryRun(Base):
    __tablename__ = "summary_run"

    id = Column(UUID(as_uuid=False), primary_key=True, index=True)
    flow_id = Column(UUID(as_uuid=False), ForeignKey("flow.id", ondelete="CASCADE"), nullable=False)
    thread_id = Column(UUID(as_uuid=False), ForeignKey("thread.id", ondelete="SET NULL"), nullable=True)
    flow_summary_id = Column(UUID(as_uuid=False), ForeignKey("flow_summary.id", ondelete="SET NULL"), nullable=True)
    stage = Column(String, nullable=False)  # collect|chunk|summarize|merge|commit
    status = Column(String, nullable=False, default="queued")  # queued|running|succeeded|failed
    source = Column(JSON, nullable=False)
    result = Column(JSON, nullable=True)
    error = Column(String, nullable=True)
    cost = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    # Relations
    flow = relationship("Flow", back_populates="summary_runs")
    thread = relationship("Thread", back_populates="summary_runs")
    flow_summary = relationship("FlowSummary", back_populates="summary_runs")

class PromptTemplate(Base):
    __tablename__ = "prompt_template"

    key = Column(String, primary_key=True, index=True)
    text = Column(String, nullable=False)
    meta = Column(JSON, nullable=False, default=dict)
    updated_at = Column(DateTime, server_default=func.now(), nullable=False)

class SchemaUpgradePlan(Base):
    __tablename__ = "schema_upgrade_plan"

    id = Column(UUID(as_uuid=False), primary_key=True, index=True)
    name = Column(String, nullable=False)
    from_schema_def_id = Column(UUID(as_uuid=False), ForeignKey("schema_def.id", ondelete="RESTRICT"), nullable=False)
    to_schema_def_id = Column(UUID(as_uuid=False), ForeignKey("schema_def.id", ondelete="RESTRICT"), nullable=False)
    strategy = Column(String, nullable=False, default="transform")  # transform|no_change|manual_only|deprecated
    transform_spec = Column(JSON, nullable=False, default=dict)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relations
    from_schema_def = relationship("SchemaDef", foreign_keys=[from_schema_def_id], back_populates="upgrade_plans_from")
    to_schema_def = relationship("SchemaDef", foreign_keys=[to_schema_def_id], back_populates="upgrade_plans_to")
    upgrade_runs = relationship("PipelineUpgradeRun", back_populates="upgrade_plan")

class PipelineUpgradeRun(Base):
    __tablename__ = "pipeline_upgrade_run"

    id = Column(UUID(as_uuid=False), primary_key=True, index=True)
    pipeline_id = Column(UUID(as_uuid=False), ForeignKey("pipeline.id", ondelete="CASCADE"), nullable=False)
    from_schema_def_id = Column(UUID(as_uuid=False), ForeignKey("schema_def.id", ondelete="RESTRICT"), nullable=False)
    to_schema_def_id = Column(UUID(as_uuid=False), ForeignKey("schema_def.id", ondelete="RESTRICT"), nullable=False)
    upgrade_plan_id = Column(UUID(as_uuid=False), ForeignKey("schema_upgrade_plan.id", ondelete="SET NULL"), nullable=True)
    status = Column(String, nullable=False, default="queued")  # queued|running|succeeded|failed|skipped
    mode = Column(String, nullable=False, default="auto")  # auto|assisted|manual
    diff = Column(JSON, nullable=True)
    issues = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    # Relations
    pipeline = relationship("Pipeline")
    from_schema_def = relationship("SchemaDef", foreign_keys=[from_schema_def_id])
    to_schema_def = relationship("SchemaDef", foreign_keys=[to_schema_def_id])
    upgrade_plan = relationship("SchemaUpgradePlan", back_populates="upgrade_runs")

class CompatRule(Base):
    __tablename__ = "compat_rule"

    id = Column(UUID(as_uuid=False), primary_key=True, index=True)
    schema_def_id = Column(UUID(as_uuid=False), ForeignKey("schema_def.id", ondelete="CASCADE"), nullable=False)
    compatible_with = Column(ARRAY(String), nullable=False, default=list)
    notes = Column(String, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relations
    schema_def = relationship("SchemaDef", back_populates="compat_rules")

class AgentLog(Base):
    __tablename__ = "agent_log"

    id = Column(UUID(as_uuid=False), primary_key=True, index=True)
    flow_id = Column(UUID(as_uuid=False), ForeignKey("flow.id", ondelete="SET NULL"), nullable=True)
    thread_id = Column(UUID(as_uuid=False), ForeignKey("thread.id", ondelete="SET NULL"), nullable=True)
    level = Column(String, nullable=False)
    event = Column(String, nullable=False)
    data = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relations
    flow = relationship("Flow", back_populates="logs")
    thread = relationship("Thread", back_populates="logs")
