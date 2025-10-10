from __future__ import annotations

from typing import Iterable, Dict
from ..core.ports import PipelineRepo, FlowRepo
from ..core.errors import NotFound, ValidationFailed
from ..app_decorators import instrument_uc

@instrument_uc("CreatePipeline")
class CreatePipeline:
    def __init__(self, pipelines: PipelineRepo, flows: FlowRepo):
        self.pipelines, self.flows = pipelines, flows
    def __call__(self, *, flow_id: str, payload: Dict) -> Dict:
        if not self.flows.get(flow_id):
            raise NotFound(f"Flow {flow_id} not found")
        if not isinstance(payload, dict):
            raise ValidationFailed("pipeline payload must be dict")
        return self.pipelines.create(flow_id, payload)

@instrument_uc("ListPipelinesForFlow")
class ListPipelinesForFlow:
    def __init__(self, pipelines: PipelineRepo, flows: FlowRepo):
        self.pipelines, self.flows = pipelines, flows
    def __call__(self, *, flow_id: str, limit: int = 100, offset: int = 0) -> Iterable[Dict]:
        if not self.flows.get(flow_id):
            raise NotFound(f"Flow {flow_id} not found")
        return list(self.pipelines.list_for_flow(flow_id, limit, offset))