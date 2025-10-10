from __future__ import annotations

from ..app_decorators import instrument_uc
from typing import Dict
from ..core.ports import ThreadRepo
from ..core.errors import NotFound

class GetThread:
    @instrument_uc('GetThread')
    def __init__(self, threads: ThreadRepo):
        self.threads = threads
    def __call__(self, *, thread_id: str) -> Dict:
        t = self.threads.get(thread_id)
        if not t:
            raise NotFound(f"Thread {thread_id} not found")
        return {"id": t.id, "flow_id": t.flow_id, "status": t.status, "started_at": t.started_at, "closed_at": t.closed_at}