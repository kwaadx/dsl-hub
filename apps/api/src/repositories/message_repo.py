from sqlalchemy.orm import Session
from ..models import Message

class MessageRepo:
    def __init__(self, db: Session):
        self.db = db

    def add(self, id, thread_id, role, content, parent_id=None, tool_name=None, tool_result=None, format="text"):
        m = Message(id=id, thread_id=thread_id, role=role, content=content, parent_id=parent_id, tool_name=tool_name, tool_result=tool_result, format=format)
        self.db.add(m); self.db.flush()
        return m

    def list_for_thread(self, thread_id, limit=50):
        q = self.db.query(Message).filter(Message.thread_id==thread_id).order_by(Message.created_at.asc()).limit(limit)
        return q.all()
