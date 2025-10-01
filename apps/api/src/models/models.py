from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .database import Base

# Enums
class ThreadStatus(str, enum.Enum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"

class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"

class MessageFormat(str, enum.Enum):
    TEXT = "text"
    MARKDOWN = "markdown"
    JSON = "json"
    BUTTONS = "buttons"
    CARD = "card"

# Models
class Flow(Base):
    __tablename__ = "flows"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    threads = relationship("Thread", back_populates="flow")
    pipelines = relationship("Pipeline", back_populates="flow")
    summaries = relationship("FlowSummary", back_populates="flow")
    logs = relationship("AgentLog", back_populates="flow")

class Thread(Base):
    __tablename__ = "threads"

    id = Column(String, primary_key=True, index=True)
    flow_id = Column(String, ForeignKey("flows.id"))
    status = Column(Enum(ThreadStatus), default=ThreadStatus.NEW)
    archived = Column(Boolean, default=False)
    archived_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, server_default=func.now())
    closed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    flow = relationship("Flow", back_populates="threads")
    messages = relationship("Message", back_populates="thread")
    logs = relationship("AgentLog", back_populates="thread")

class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, index=True)
    thread_id = Column(String, ForeignKey("threads.id"))
    role = Column(Enum(MessageRole))
    format = Column(Enum(MessageFormat), default=MessageFormat.TEXT)
    content = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())

    thread = relationship("Thread", back_populates="messages")

class Pipeline(Base):
    __tablename__ = "pipelines"

    id = Column(String, primary_key=True, index=True)
    flow_id = Column(String, ForeignKey("flows.id"))
    version = Column(String)
    schema_version = Column(String)
    status = Column(String, default="draft")
    content = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    flow = relationship("Flow", back_populates="pipelines")

class SchemaDef(Base):
    __tablename__ = "schema_defs"

    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    version = Column(String)
    json = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class FlowSummary(Base):
    __tablename__ = "flow_summaries"

    id = Column(String, primary_key=True, index=True)
    flow_id = Column(String, ForeignKey("flows.id"))
    version = Column(Integer, default=1)
    content = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    flow = relationship("Flow", back_populates="summaries")

class GlobalSummary(Base):
    __tablename__ = "global_summaries"

    id = Column(String, primary_key=True, index=True)
    content = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(String, primary_key=True, index=True)
    flow_id = Column(String, ForeignKey("flows.id"), nullable=True)
    thread_id = Column(String, ForeignKey("threads.id"), nullable=True)
    level = Column(String)
    event = Column(String)
    data = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    flow = relationship("Flow", back_populates="logs")
    thread = relationship("Thread", back_populates="logs")
