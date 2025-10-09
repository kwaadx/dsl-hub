import pytest

from apps.api.src.sse import bus


@pytest.mark.asyncio
async def test_message_created_is_buffered_and_replayable():
    key = "t-buffered"
    # Publish a message.created event as the system would do
    await bus.publish(key, "message.created", {
        "message_id": "mid-1",
        "role": "assistant",
        "format": "text",
        "content": {"text": "Hello"},
    })

    # Replay from 0 should include our event
    items = await bus.replay(key, 0)
    assert items is not None
    assert any(it.get("type") == "message.created" for it in items)
