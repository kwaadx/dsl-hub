from types import SimpleNamespace
from src.application.messages import CreateMessage, ListMessages

class FakeUoW:
    def __init__(self): self.commits=0
    def __enter__(self): return self
    def __exit__(self, *a): pass
    def commit(self): self.commits+=1

class FakeThreads:
    def get(self, thread_id): return SimpleNamespace(id=thread_id)

class FakeMessages:
    def __init__(self): self.store=[]
    def create(self, **kw): self.store.append(kw); return kw | {"id":"m1"}
    def list_for_thread(self, thread_id, limit=50, before=None): 
        return list(self.store)

def test_create_and_list_message():
    cm = CreateMessage(messages=FakeMessages(), threads=FakeThreads(), uow_factory=lambda: FakeUoW())
    out = cm(thread_id="t1", payload={"role":"user","content":"hi","format":"text"})
    assert out["id"]=="m1"
    lm = ListMessages(messages=cm.messages, threads=FakeThreads())
    lst = lm(thread_id="t1", limit=10)
    assert lst and lst[0]["content"]=="hi"