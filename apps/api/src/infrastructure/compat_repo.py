from __future__ import annotations

from typing import Iterable
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models import CompatRule
from ..core.ports import CompatRuleRepo

class SACompatRuleRepo(CompatRuleRepo):
    def __init__(self, db: Session): self.db = db
    def list_for_subject(self, subject_kind: str, subject_key: str, subject_version: str) -> Iterable[dict]:
        rows = self.db.execute(
            select(CompatRule).where(
                CompatRule.subject_kind==subject_kind,
                CompatRule.subject_key==subject_key,
                CompatRule.subject_version==subject_version
            )
        ).scalars().all()
        for r in rows:
            yield {"id": str(r.id), "requires_kind": r.requires_kind, "requires_key": r.requires_key, "requires_version": r.requires_version, "rule": r.rule}