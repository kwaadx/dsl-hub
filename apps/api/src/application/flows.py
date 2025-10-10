from __future__ import annotations

from typing import Optional, Iterable, Dict
from ..core.ports import FlowRepo
from ..core.errors import NotFound, ValidationFailed
from ..app_decorators import instrument_uc

@instrument_uc("ListFlows")
class ListFlows:
    def __init__(self, flows: FlowRepo):
        self.flows = flows
    def __call__(self, *, limit: int = 100, offset: int = 0) -> Iterable[Dict]:
        return list(self.flows.list(limit=limit, offset=offset))

@instrument_uc("CreateFlow")
class CreateFlow:
    def __init__(self, flows: FlowRepo):
        self.flows = flows
    def __call__(self, *, name: str, slug: Optional[str]) -> Dict:
        if not name or len(name.strip())<1:
            raise ValidationFailed("name is required")
        return self.flows.create(name=name.strip(), slug=slug)

@instrument_uc("UpdateFlow")
class UpdateFlow:
    def __init__(self, flows: FlowRepo):
        self.flows = flows
    def __call__(self, *, flow_id: str, name: Optional[str], slug: Optional[str]) -> Dict:
        if not self.flows.get(flow_id):
            raise NotFound(f"Flow {flow_id} not found")
        return self.flows.update(flow_id, name=name, slug=slug)

@instrument_uc("DeleteFlow")
class DeleteFlow:
    def __init__(self, flows: FlowRepo):
        self.flows = flows
    def __call__(self, *, flow_id: str) -> bool:
        return self.flows.delete(flow_id)