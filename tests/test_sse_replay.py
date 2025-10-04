import asyncio
import pytest

from apps.api.src.sse import bus


@pytest.mark.asyncio
async def test_can_replay_window():
    key = "t-xyz"
    # Publish a few events
    await bus.publish(key, "e1", {"a": 1})  # cursor 1
    await bus.publish(key, "e2", {"a": 2})  # cursor 2
    await bus.publish(key, "e3", {"a": 3})  # cursor 3

    # Fresh clients with Last-Event-ID=0 can replay (>= earliest-1)
    assert await bus.can_replay(key, 0) is True

    # Too old cursor should not be replayable
    assert await bus.can_replay(key, -100) is False

    # Latest cursor can replay nothing but is valid
    assert await bus.can_replay(key, 3) is True
