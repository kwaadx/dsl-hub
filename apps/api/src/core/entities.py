from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Any

@dataclass(frozen=True, slots=True)
class ThreadEntity:
    id: str
    flow_id: str
    status: str
    started_at: str
    closed_at: Optional[str] = None

@dataclass(frozen=True, slots=True)
class MessageEntity:
    id: str
    thread_id: str
    role: str
    format: str
    content: Any
    created_at: str
    parent_id: Optional[str] = None