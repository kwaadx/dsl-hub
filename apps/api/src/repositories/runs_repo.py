from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

from sqlalchemy.orm import Session
from ..models import GenerationRun, ValidationIssue
from typing import Optional, List, Dict, Any
from datetime import datetime, UTC

class RunsRepo:
    def __init__(self, db: Session):
        self.db = db

    def start(self, run_id: str, flow_id: str, thread_id: str, stage: str, source: Dict[str, Any]) -> GenerationRun:
        """Create a GenerationRun row ensuring timestamp ordering constraints.
        We avoid setting started_at before created_at is populated by the DB.
        """
        run = GenerationRun(
            id=run_id,
            flow_id=flow_id,
            thread_id=thread_id,
            stage=stage,
            status="running",
            source=source,
            # defer started_at until after insert to satisfy CHECK(created_at <= started_at)
            started_at=None,
        )
        self.db.add(run)
        self.db.flush()
        # Now that created_at is set by DB, set started_at to created_at (or now, whichever is later)
        try:
            self.db.refresh(run)
            created = getattr(run, "created_at", None)
            if created is not None:
                run.started_at = created
            else:
                run.started_at = datetime.now(UTC)
            self.db.flush()
        except Exception:
            # Best-effort fallback; still try to set started_at to a sane value
            run.started_at = datetime.now(UTC)
            self.db.flush()
        return run

    def tick(self, run_id: str, stage: str, status: str = "running", result: Optional[Dict[str, Any]] = None, error: Optional[str] = None) -> GenerationRun | None:
        run = self.db.get(GenerationRun, run_id)
        if not run:
            return None
        # If stage changes and caller immediately requests a terminal status (succeeded/failed),
        # perform a two-step transition to satisfy DB CHECK constraints: set stage with "running"
        # first, then mark the terminal status. This mirrors the real lifecycle and avoids
        # violations like generation_run_stage_ck.
        stage_changed = (run.stage != stage)
        terminal = status in ("succeeded", "failed")
        if stage_changed and terminal:
            # Step 1: enter the new stage as running
            run.stage = stage
            run.status = "running"
            self.db.flush()
            # Step 2: finalize the stage with requested terminal status
            run.status = status
            if result is not None:
                run.result = result
            if error:
                run.error = error
            self.db.flush()
            return run
        # Default: single-step update
        run.stage = stage
        run.status = status
        if result is not None:
            run.result = result
        if error:
            run.error = error
        self.db.flush()
        return run

    def finish(self, run_id: str, status: str = "succeeded") -> GenerationRun | None:
        run = self.db.get(GenerationRun, run_id)
        if not run:
            return None
        run.status = status
        run.finished_at = datetime.now(UTC)
        self.db.flush()
        return run

    def add_issues(self, run_id: str, issues: List[Dict[str, Any]]) -> None:
        for it in issues:
            vi = ValidationIssue(
                generation_run_id=run_id,
                path=it.get("path", "/"),
                code=it.get("code", "unknown"),
                severity=it.get("severity", "error"),
                message=it.get("message", ""),
            )
            self.db.add(vi)
        self.db.flush()
