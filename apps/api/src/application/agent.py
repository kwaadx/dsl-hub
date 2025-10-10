from __future__ import annotations

from ..app_decorators import instrument_uc
from ..tracing import traced
from typing import Dict, Any, Optional
from ..agent.graph import AgentRunner

class StartAgentRun:
    @instrument_uc('StartAgentRun')
    @traced('agent.start')
    def __init__(self, runner: AgentRunner):
        self.runner = runner
    async def __call__(self, *, flow_id: str, thread_id: str, user_message: Dict[str, Any], options: Optional[Dict[str, Any]] = None, run_id: Optional[str] = None) -> str:
        return await self.runner.run(flow_id=flow_id, thread_id=thread_id, user_message=user_message, options=options, run_id=run_id)