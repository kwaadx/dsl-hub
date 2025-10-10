import asyncio
from types import SimpleNamespace

class FakeLLM:
    def __init__(self): self.calls=[]
    async def chat(self, messages, *, timeout=None):
        self.calls.append(messages); return {"choices":[{"message":{"role":"assistant","content":"ok"}}]}

class FakeSimilarity: 
    def score(self, a,b): return 0.9

class FakeValSvc:
    def __init__(self):
        self.schemas = SimpleNamespace(get_active_schema=lambda channel: {"version":"2"})

class FakeRuns: 
    def create(self, *a, **k): pass
    def update_status(self, *a, **k): pass
    def get(self, *a, **k): return {"run_id":"r1","status":"done"}

class FakePipe:
    def get_active_for_flow(self, flow_id): return {"version":"2"}
    def compile(self, pipeline): return {"ok": True}

class FakePrompts:
    def get_active(self, key):
        mapping = {
            "agent.plan": {"content":{"system":"PLAN"}},
            "agent.act": {"content":{"system":"ACT"}},
            "agent.reflect": {"content":{"system":"REFLECT"}},
            "agent.default": {"content":{"system":"DEFAULT"}},
        }
        return mapping.get(key)

class FakeCompat:
    def list_for_subject(self, *a, **k):
        return [{"requires_kind":"schema","requires_key":"messages","requires_version":"2","rule":{"op":">="}}]

class FakeLog:
    def __init__(self): self.events=[]
    def write(self, run_id, thread_id, flow_id, step, level, message, data=None):
        self.events.append((step, level))

async def _run():
    from src.agent.graph import AgentRunner
    llm = FakeLLM()
    ar = AgentRunner(session_factory=lambda: None, similarity_service=FakeSimilarity(), llm_client=llm,
                     runs_repo=FakeRuns(), pipeline_service=FakePipe(), validation_service=FakeValSvc(),
                     prompt_repo=FakePrompts(), compat_repo=FakeCompat(), agent_log=FakeLog())
    await ar.run(flow_id="f1", thread_id="t1", user_message={"role":"user","content":"hi"}, options=None, run_id="r1")
    # We can't assert exact call sites, but ensure at least one message starts with stage system prompt
    flat = [m for call in llm.calls for m in call]
    assert any(m.get("role")=="system" and m.get("content") in ("PLAN","ACT","REFLECT","DEFAULT") for m in flat)

def test_agent_e2e():
    asyncio.get_event_loop().run_until_complete(_run())