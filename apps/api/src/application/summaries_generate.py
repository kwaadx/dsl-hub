from __future__ import annotations

from typing import Dict, Any, List, Optional
from ..core.ports import MessageRepo, ThreadRepo, ThreadSummaryRepo, FlowSummaryRepo, SummarizerPort
from ..core.errors import NotFound, ValidationFailed
from ..app_decorators import instrument_uc

@instrument_uc("GenerateThreadSummary")
class GenerateThreadSummary:
    def __init__(self, messages: MessageRepo, threads: ThreadRepo, ts_repo: ThreadSummaryRepo, summarizer: SummarizerPort):
        self.messages, self.threads, self.ts_repo, self.summarizer = messages, threads, ts_repo, summarizer
    async def __call__(self, *, thread_id: str, kind: str = "short") -> Dict[str, Any]:
        t = self.threads.get(thread_id)
        if not t: raise NotFound(f"Thread {thread_id} not found")
        msgs = list(self.messages.list_for_thread(thread_id, limit=200))
        # Convert to LLM-friendly format
        llm_msgs = [{"role": m["role"] if isinstance(m, dict) else getattr(m, "role", "user"),
                     "content": (m["content"] if isinstance(m, dict) else getattr(m, "content", ""))} for m in msgs]
        res = await self.summarizer.summarize_thread(llm_msgs, kind=kind)
        created = self.ts_repo.create(thread_id, kind=kind, content=res["content"], token_budget=1024, covering_from=None, covering_to=None)
        return created

@instrument_uc("RefreshFlowSummary")
class RefreshFlowSummary:
    def __init__(self, ts_repo: ThreadSummaryRepo, fs_repo: FlowSummaryRepo, summarizer: SummarizerPort):
        self.ts_repo, self.fs_repo, self.summarizer = ts_repo, fs_repo, summarizer
    async def __call__(self, *, flow_id: str, thread_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        # Collect recent thread summaries across provided thread_ids (or all, if repo supports listing by flow)
        # For now, if thread_ids not provided, return active as-is
        summaries: List[dict] = []
        if thread_ids:
            for tid in thread_ids:
                summaries.extend(list(self.ts_repo.list_for_thread(tid))[:1])  # pick latest per thread
        if not summaries:
            # fallback to existing active flow summary payload
            current = self.fs_repo.get_active(flow_id)
            return current or {"version": 0, "content": {}, "last_message_id": None}
        res = await self.summarizer.summarize_flow(summaries)
        out = self.fs_repo.upsert_active(flow_id, content=res["content"], last_message_id=None)
        return out