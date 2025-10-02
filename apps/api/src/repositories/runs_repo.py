from sqlalchemy.orm import Session
from ..models import GenerationRun, ValidationIssue
from typing import Optional, List, Dict, Any
from datetime import datetime, UTC

class RunsRepo:
    def __init__(self, db: Session):
        self.db = db

    def start(self, run_id: str, flow_id: str, thread_id: str, stage: str, source: Dict[str, Any]) -> GenerationRun:
        run = GenerationRun(id=run_id, flow_id=flow_id, thread_id=thread_id, stage=stage, status="running", source=source, started_at=datetime.now(UTC))
        self.db.add(run); self.db.flush()
        return run

    def tick(self, run_id: str, stage: str, status: str = "running", result: Optional[Dict[str, Any]] = None, error: Optional[str] = None) -> GenerationRun:
        run = self.db.get(GenerationRun, run_id)
        run.stage = stage
        run.status = status
        if result is not None:
            run.result = result
        if error:
            run.error = error
        self.db.flush()
        return run

    def finish(self, run_id: str, status: str = "succeeded") -> GenerationRun:
        run = self.db.get(GenerationRun, run_id)
        run.status = status
        run.finished_at = datetime.now(UTC)
        self.db.flush()
        return run

    def add_issues(self, run_id: str, issues: List[Dict[str, Any]]) -> None:
        for it in issues:
            vi = ValidationIssue(generation_run_id=run_id, path=it.get("path","/"), code=it.get("code","unknown"), severity=it.get("severity","error"), message=it.get("message",""))
            self.db.add(vi)
        self.db.flush()
