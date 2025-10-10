from __future__ import annotations

from typing import Iterable
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models import PromptTemplate
from ..core.ports import PromptTemplateRepo

class SAPromptTemplateRepo(PromptTemplateRepo):
    def __init__(self, db: Session): self.db = db
    def get_active(self, key: str) -> dict | None:
        row = self.db.execute(
            select(PromptTemplate).where(PromptTemplate.key==key, PromptTemplate.is_active==True).order_by(PromptTemplate.version.desc())  # noqa: E712
        ).scalar_one_or_none()
        return row and {"id": str(row.id), "key": row.key, "version": row.version, "content": row.content, "is_active": row.is_active}
    def get(self, key: str, version: int) -> dict | None:
        row = self.db.execute(
            select(PromptTemplate).where(PromptTemplate.key==key, PromptTemplate.version==version)
        ).scalar_one_or_none()
        return row and {"id": str(row.id), "key": row.key, "version": row.version, "content": row.content, "is_active": row.is_active}
    def list(self, key: str) -> Iterable[dict]:
        rows = self.db.execute(select(PromptTemplate).where(PromptTemplate.key==key).order_by(PromptTemplate.version.desc())).scalars().all()
        for r in rows:
            yield {"id": str(r.id), "key": r.key, "version": r.version, "content": r.content, "is_active": r.is_active}
    def upsert(self, key: str, version: int, content: dict, is_active: bool = True) -> dict:
        from uuid import uuid4
        row = self.db.execute(select(PromptTemplate).where(PromptTemplate.key==key, PromptTemplate.version==version)).scalar_one_or_none()
        if row:
            row.content = content; row.is_active = is_active
            self.db.add(row)
        else:
            row = PromptTemplate(id=str(uuid4()), key=key, version=version, content=content, is_active=is_active)
            self.db.add(row)
        self.db.flush(); self.db.refresh(row)
        return {"id": str(row.id), "key": row.key, "version": row.version, "content": row.content, "is_active": row.is_active}