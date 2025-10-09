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

class UpdateFlow(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    slug: Optional[str] = Field(default=None, min_length=1, max_length=100, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

class CreateThread(BaseModel):
    pass

class ThreadOut(BaseModel):
    id: str
    flow_id: str
    status: str
    started_at: str
    closed_at: Optional[str] = None

class MessageIn(BaseModel):
    role: str
    content: Any
    format: str = "text"
    parent_id: Optional[str] = None
    tool_name: Optional[str] = None
    tool_result: Optional[Any] = None

class MessageOut(BaseModel):
    id: str
    created_at: str

class AgentRunIn(BaseModel):
    user_message: Any
    options: dict = Field(default_factory=dict)

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

class SchemaDefBrief(BaseModel):
    id: str
    name: str
    version: str

class SchemaChannelOut(BaseModel):
    name: str
    active_schema_def_id: str
    def_: Optional[SchemaDefBrief] = Field(default=None, alias="def")

    class Config:
        populate_by_name = True

# --- UI Events DTOs ---
class UIEventIn(BaseModel):
    kind: str
    msgId: Optional[str] = None
    actionId: Optional[str] = None
    payload: Optional[Any] = None
    url: Optional[str] = None

class UIEventAck(BaseModel):
    ok: bool = True
