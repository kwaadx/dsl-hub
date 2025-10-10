import asyncio
from types import SimpleNamespace
from src.application.summaries_generate import GenerateThreadSummary, RefreshFlowSummary

class FakeMsgRepo:
    def list_for_thread(self, thread_id, limit=200):
        return [dict(role="user", content="hello"), dict(role="assistant", content="world")]
class FakeThreads:
    def get(self, thread_id): return SimpleNamespace(id=thread_id, flow_id="f1")
class FakeTSRepo:
    def __init__(self): self.last=None
    def create(self, thread_id, *, kind, content, token_budget, covering_from, covering_to):
        self.last = dict(thread_id=thread_id, kind=kind, content=content); return self.last
    def list_for_thread(self, thread_id):
        return [dict(kind="short", content={"summary": "ok"})]
class FakeFSRepo:
    def __init__(self): self.last=None
    def get_active(self, flow_id): return None
    def upsert_active(self, flow_id, *, content, last_message_id): self.last={"flow_id":flow_id,"content":content}; return self.last
class FakeSummarizer:
    async def summarize_thread(self, messages, *, kind="short"): return {"content":{"summary":"sth","bullets":["a","b"]}}
    async def summarize_flow(self, thread_summaries): return {"content":{"summary":"flow","bullets":["x"]}}
class FakeBus:
    def __init__(self): self.events=[]
    def publish(self, data, *, channel=None): self.events.append((channel, data.get("kind")))

async def _run():
    ts = FakeTSRepo(); fs = FakeFSRepo(); bus = FakeBus()
    gt = GenerateThreadSummary(FakeMsgRepo(), FakeThreads(), ts, FakeSummarizer(), bus)
    out = await gt(thread_id="t1", kind="short")
    assert out["thread_id"]=="t1"
    assert ("thread:t1","thread_summary_created") in bus.events

    rf = RefreshFlowSummary(ts, fs, FakeSummarizer(), bus)
    out2 = await rf(flow_id="f1", thread_ids=["t1"])
    assert out2["flow_id"]=="f1"
    assert ("flow:f1","flow_summary_refreshed") in bus.events

def test_summaries_flows_thread():
    asyncio.get_event_loop().run_until_complete(_run())