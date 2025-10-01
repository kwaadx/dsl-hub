from pydantic import BaseModel, Field
from typing import Optional, Any, List

class CreateFlow(BaseModel):
    slug: str
    name: str

class FlowOut(BaseModel):
    id: str
    slug: str
    name: str
    has_published: bool = False
    active_version: Optional[str] = None

class CreateThread(BaseModel):
    pass

class ThreadOut(BaseModel):
    id: str
    flow_id: str
    status: str
    started_at: str

class MessageIn(BaseModel):
    role: str
    content: Any
    format: Optional[str] = "text"
    parent_id: Optional[str] = None
    tool_name: Optional[str] = None
    tool_result: Optional[Any] = None

class MessageOut(BaseModel):
    id: str
    created_at: str

class AgentRunIn(BaseModel):
    user_message: Any
    options: Optional[dict] = Field(default_factory=dict)

class AgentRunAck(BaseModel):
    run_id: str
    status: str

class SuggestionOut(BaseModel):
    ok: bool = False
    suggestion: dict

class DraftOkOut(BaseModel):
    ok: bool = True
    pipeline_id: str
    version: str
    status: str

class IssuesOut(BaseModel):
    ok: bool = False
    issues: List[dict]

class PublishAck(BaseModel):
    ok: bool = True
    flow_id: str
    version: str
    is_published: bool = True
