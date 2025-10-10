from __future__ import annotations

from ..core.ports import EventBusPort
from ..sse import bus

class SSEEventBus(EventBusPort):
    def publish(self, data: dict, *, channel: str | None = None) -> None:
        bus.publish(data, channel=channel)