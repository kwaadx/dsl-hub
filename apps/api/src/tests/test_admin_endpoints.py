from fastapi.testclient import TestClient
from types import SimpleNamespace

# Import app and deps to override
from src.main import app
from src.deps import prompt_repo as dep_prompt_repo, compat_repo as dep_compat_repo
from src.deps import db_session as dep_db_session
from src.models import AgentLog
from datetime import datetime

# ---- Fakes ----
class FakePromptRepo:
    def __init__(self): self.data = {}
    def get_active(self, key):
        versions = self.data.get(key, [])
        for row in versions:
            if row["is_active"]:
                return {"id":"1","key":key, "version":row["version"], "content":row["content"], "is_active": True}
        return None
    def get(self, key, version): 
        for row in self.data.get(key, []):
            if row["version"]==version: return row
        return None
    def list(self, key):
        return list(self.data.get(key, []))
    def upsert(self, key, version, content, is_active=True):
        arr = self.data.setdefault(key, [])
        for row in arr:
            if row["version"]==version:
                row.update({"content":content,"is_active":is_active})
                return row
        row = {"id":"x","key":key,"version":version,"content":content,"is_active":is_active}
        arr.append(row)
        if is_active:
            for r in arr:
                if r is not row: r["is_active"]=False
        return row

class FakeCompatRepo:
    def list_for_subject(self, subject_kind, subject_key, subject_version):
        return [{"id":"1","requires_kind":"schema","requires_key":"messages","requires_version":"2","rule":{"op":">="}}]

class FakeResult:
    def __init__(self, rows): self._rows = rows
    def scalars(self): return self
    def all(self): return self._rows

class FakeSession:
    def __init__(self): 
        self._rows = [SimpleNamespace(id="1", run_id="r1", thread_id="t1", flow_id="f1", step="x", level="info", message="ok", data={"a":1}, created_at=datetime.utcnow())]
    def execute(self, *a, **k): return FakeResult(self._rows)

# ---- Overrides ----
app.dependency_overrides[dep_prompt_repo] = lambda: FakePromptRepo()
app.dependency_overrides[dep_compat_repo] = lambda: FakeCompatRepo()
app.dependency_overrides[dep_db_session] = lambda: FakeSession()

client = TestClient(app)

def test_admin_prompts_crud_and_active():
    # upsert v1 active
    r = client.post("/admin/prompts/agent.default", json={"version":1,"content":{"system":"SYS1"},"is_active":True})
    assert r.status_code==200
    # list
    r = client.get("/admin/prompts/agent.default")
    assert r.status_code==200 and len(r.json())==1
    # get active
    r = client.get("/admin/prompts/agent.default/active")
    assert r.status_code==200 and r.json()["content"]["system"]=="SYS1"

def test_admin_compat_list():
    r = client.get("/admin/compat/pipeline/myflow/1")
    assert r.status_code==200 and isinstance(r.json(), list)

def test_agent_logs_endpoints():
    r = client.get("/agent/logs/by-run/r1"); assert r.status_code==200 and len(r.json())>=1
    r = client.get("/agent/logs/by-thread/t1"); assert r.status_code==200 and len(r.json())>=1