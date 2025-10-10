from __future__ import annotations

from sqlalchemy.orm import Session
from ..core.uow import UnitOfWork

class SAUnitOfWork(UnitOfWork):
    def __init__(self, session: Session):
        self.session = session
    def commit(self) -> None:
        self.session.commit()
    def rollback(self) -> None:
        self.session.rollback()