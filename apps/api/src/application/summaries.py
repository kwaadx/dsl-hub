from __future__ import annotations

from typing import Iterable, Dict
from ..core.ports import ThreadSummaryRepo
from ..app_decorators import instrument_uc

@instrument_uc("ListThreadSummaries")
class ListThreadSummaries:
    def __init__(self, repo: ThreadSummaryRepo):
        self.repo = repo
    def __call__(self, *, thread_id: str) -> Iterable[Dict]:
        return list(self.repo.list_for_thread(thread_id))