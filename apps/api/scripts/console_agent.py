#!/usr/bin/env python3
"""
Console chat with DSL Hub agent (in-process).

Usage examples:
  python apps/api/scripts/console_agent.py --create-flow
  python apps/api/scripts/console_agent.py --flow-id <existing_flow_id>
  python apps/api/scripts/console_agent.py --flow-id <id> --thread-id <thread>
  python apps/api/scripts/console_agent.py --create-flow --publish

Tips:
- Set LLM_PROVIDER=mock for offline testing (no external API key needed).
- Ensure DB env vars are configured (see apps/api/README.md or repo root README).
"""
import asyncio
import argparse
import contextlib
import os
import sys
from typing import Any, Dict

# Ensure repository root is importable when running directly
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.sse import bus  # noqa: E402
from src.agent.graph import AgentRunner  # noqa: E402
from src.database import SessionLocal  # noqa: E402
from src.services.flow_service import FlowService  # noqa: E402
from src.services.thread_service import ThreadService  # noqa: E402


async def stream_events(thread_id: str) -> None:
    """Subscribe to the internal SSE bus and print events for the thread."""
    q, _ = await bus.subscribe(thread_id)
    try:
        while True:
            item = await q.get()
            et = item.get("type")
            data = item.get("data")
            cursor = item.get("cursor")
            ts = item.get("ts")

            if et in {"agent.msg"}:
                role = (data or {}).get("role") if isinstance(data, dict) else None
                fmt = (data or {}).get("format") if isinstance(data, dict) else None
                content = (data or {}).get("content") if isinstance(data, dict) else data
                if isinstance(content, dict) and "text" in content:
                    text = content.get("text")
                else:
                    text = str(content)
                print(f"[{cursor}][{ts}] {role or 'assistant'}({fmt}): {text}")
            elif et in {"run.started", "run.stage", "run.finished"}:
                print(f"[{cursor}][{ts}] {et}: {data}")
            elif et in {"suggestion", "issues", "pipeline.created", "pipeline.published"}:
                print(f"[{cursor}][{ts}] {et}: {data}")
            else:
                print(f"[{cursor}][{ts}] {et}: {data}")
    finally:
        await bus.unsubscribe(thread_id, q)


async def ensure_flow(db, flow_id: str | None, slug: str | None, name: str | None, create_if_needed: bool) -> str:
    svc = FlowService(db)
    if flow_id:
        f = svc.get_one(flow_id)
        if f:
            return f["id"]
        if not create_if_needed:
            raise SystemExit(f"Flow {flow_id} not found. Pass --create-flow to create a test flow.")
    if not create_if_needed:
        # If no flow_id specified — pick the first available
        lst = svc.list()
        if not lst:
            raise SystemExit("No flows found. Use --create-flow to create a test flow.")
        return lst[0]["id"]
    # create
    slug = slug or "console-test"
    name = name or "Console Test Flow"
    f = svc.create(slug, name)
    return f["id"]


async def ensure_thread(db, flow_id: str, thread_id: str | None) -> str:
    # If thread_id not provided — create a new one
    if thread_id:
        return thread_id
    ts = ThreadService(db)
    t = ts.create(flow_id)
    return t["id"]


async def run_console(flow_id: str | None, thread_id: str | None, create_flow: bool, slug: str | None, name: str | None, publish: bool) -> None:
    # 1) Prepare DB/ids
    db = SessionLocal()
    try:
        flow_id = await ensure_flow(db, flow_id, slug, name, create_if_needed=create_flow)
        thread_id = await ensure_thread(db, flow_id, thread_id)
    finally:
        db.close()

    print("\nConsole agent chat")
    print(f"Flow ID:   {flow_id}")
    print(f"Thread ID: {thread_id}")
    print("Type your message and press Enter. Ctrl+C to exit.\n")

    # 2) Start SSE event stream task
    events_task = asyncio.create_task(stream_events(thread_id))

    # 3) REPL: read input and call agent
    agent = AgentRunner()
    try:
        loop = asyncio.get_event_loop()
        while True:
            user_text = await loop.run_in_executor(None, lambda: input("You: ").strip())
            if not user_text:
                continue
            user_message: Dict[str, Any] = {"role": "user", "content": user_text}
            options: Dict[str, Any] = {"publish": bool(publish)}
            run_id = await agent.run(flow_id=flow_id, thread_id=thread_id, user_message=user_message, options=options)
            print(f"(run_id={run_id})")
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        events_task.cancel()
        with contextlib.suppress(Exception):
            await events_task


def main() -> None:
    parser = argparse.ArgumentParser(description="Console chat with DSL Hub agent")
    parser.add_argument("--flow-id", help="Existing flow id", default=None)
    parser.add_argument("--thread-id", help="Existing thread id (optional)", default=None)
    parser.add_argument("--create-flow", help="Create a test flow if none exists or id not found", action="store_true")
    parser.add_argument("--slug", help="Slug for test flow (when creating)", default=None)
    parser.add_argument("--name", help="Name for test flow (when creating)", default=None)
    parser.add_argument("--publish", help="Ask agent to publish generated pipeline", action="store_true")

    args = parser.parse_args()

    asyncio.run(
        run_console(
            flow_id=args.flow_id,
            thread_id=args.thread_id,
            create_flow=args.create_flow,
            slug=args.slug,
            name=args.name,
            publish=args.publish,
        )
    )


if __name__ == "__main__":
    main()
