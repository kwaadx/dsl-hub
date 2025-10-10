from __future__ import annotations
from sqlalchemy.orm import Session
from ..repositories.runs_repo import RunsRepo as LegacyRunsRepo
from ..services.pipeline_service import PipelineService as LegacyPipelineService
from ..services.validation_service import ValidationService as LegacyValidationService
from ..core.ports import RunsRepo as RunsRepoPort, PipelineServicePort, ValidationServicePort

class SARunsRepo(RunsRepoPort):
    def __init__(self, db: Session): self.repo = LegacyRunsRepo(db)
    def create(self, thread_id: str, run_id: str, status: str, meta: dict) -> None:
        self.repo.create(thread_id, run_id, status, meta)
    def update_status(self, run_id: str, status: str, meta: dict | None = None) -> None:
        self.repo.update_status(run_id, status, meta or {})
    def get(self, run_id: str) -> dict | None:
        r = self.repo.get(run_id)
        return r and {"run_id": r.run_id, "status": r.status, "thread_id": r.thread_id, "meta": r.meta}

class PipelineServiceAdapter(PipelineServicePort):
    def __init__(self, db: Session): self.svc = LegacyPipelineService(db)
    def get_active_for_flow(self, flow_id: str) -> dict | None:
        return self.svc.get_active_for_flow(flow_id)
    def compile(self, pipeline: dict) -> dict:
        return self.svc.compile(pipeline)

class ValidationServiceAdapter(ValidationServicePort):
    def __init__(self, db: Session): self.svc = LegacyValidationService(db)
    def validate(self, channel: str, payload: dict) -> dict:
        return self.svc.validate(channel, payload)