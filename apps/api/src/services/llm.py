"""
LLM abstraction with pluggable providers.
Default: mock generator. If settings.LLM_PROVIDER == "openai", uses OpenAI Chat Completions.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any, Optional, Dict

from ..config import settings
from ..metrics import LLM_CALLS, LLM_LATENCY

try:
    # Import lazily; only required when provider is openai
    from openai import AsyncOpenAI
    from openai import OpenAIError  # type: ignore
except ImportError:  # pragma: no cover
    AsyncOpenAI = None  # type: ignore
    OpenAIError = Exception  # type: ignore


def _ensure_json(text: str) -> Dict:
    """Extract JSON object from a model output. Tolerates code fences."""
    s = text.strip()
    # strip code fences if present
    if s.startswith("```"):
        # remove first fence line and optional language tag
        s = s.split("\n", 1)[1] if "\n" in s else s
        if s.startswith("{") is False and "\n" in s:
            # some models put language tag like ```json
            s = s.split("\n", 1)[1]
        if s.rstrip().endswith("```"):
            s = s.rsplit("```", 1)[0]
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        # Fallback minimal pipeline if parsing fails
        return {
            "name": "example-pipeline",
            "stages": [
                {"name": "load", "type": "source", "params": {"path": "s3://bucket/key"}},
                {"name": "transform", "type": "map", "params": {"fn": "clean_text"}},
                {"name": "save", "type": "sink", "params": {"table": "results"}},
            ],
        }


class LLMClient:
    def __init__(self):
        self.provider = (settings.__dict__.get("LLM_PROVIDER") or "mock").lower()
        self.timeout = int(getattr(settings, "LLM_TIMEOUT", 30))
        self._client: Optional[Any] = None
        if self.provider == "openai":
            if AsyncOpenAI is None:
                # Library missing; degrade to mock
                self.provider = "mock"
            else:
                api_key = getattr(settings, "OPENAI_API_KEY", None)
                base_url = getattr(settings, "OPENAI_BASE_URL", None) or None
                if not api_key:
                    # No key configured; degrade to mock
                    self.provider = "mock"
                else:
                    self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        # model name (used by openai provider)
        self.model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")

    async def generate_pipeline(self, context: dict, user_message: dict) -> dict:
        method = "generate_pipeline"
        provider = self.provider
        if provider != "openai":
            # mock path
            out = {
                "name": "example-pipeline",
                "stages": [
                    {"name": "load", "type": "source", "params": {"path": "s3://bucket/key"}},
                    {"name": "transform", "type": "map", "params": {"fn": "clean_text"}},
                    {"name": "save", "type": "sink", "params": {"table": "results"}},
                ],
            }
            try:
                LLM_CALLS.labels(method=method, provider=provider, status="ok").inc()
                # don't observe 0 to avoid bins artifact
                LLM_LATENCY.labels(method=method, provider=provider).observe(0.0001)
            except Exception:
                pass
            return out
        # OpenAI provider with retry/backoff
        assert self._client is not None
        system = (
            "You are an expert DSL pipeline author. Always respond with pure JSON (no extra text).\n"
            "Given schema_def (JSON Schema), optional flow_summary, and optional active_pipeline, and the user's message,\n"
            "produce a valid pipeline JSON that conforms to the schema."
        )
        user = json.dumps({
            "schema_def": context.get("schema_def"),
            "flow_summary": context.get("flow_summary"),
            "active_pipeline": context.get("active_pipeline"),
            "user_message": user_message,
        }, ensure_ascii=False)
        attempts = int(getattr(settings, "LLM_RETRIES", 3))
        backoff = 0.5
        for i in range(attempts):
            start = asyncio.get_event_loop().time()
            try:
                resp = await asyncio.wait_for(
                    self._client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system},
                            {"role": "user", "content": user},
                        ],
                        temperature=0.2,
                        response_format={"type": "json_object"},
                    ),
                    timeout=self.timeout,
                )
                content = resp.choices[0].message.content or "{}"
                out = _ensure_json(content)
                try:
                    dur = asyncio.get_event_loop().time() - start
                    LLM_CALLS.labels(method=method, provider=provider, status="ok").inc()
                    LLM_LATENCY.labels(method=method, provider=provider).observe(dur)
                except Exception:
                    pass
                return out
            except (asyncio.TimeoutError, OpenAIError):
                try:
                    dur = asyncio.get_event_loop().time() - start
                    LLM_CALLS.labels(method=method, provider=provider, status="error").inc()
                    LLM_LATENCY.labels(method=method, provider=provider).observe(dur)
                except Exception:
                    pass
                if i < attempts - 1:
                    # exponential backoff with jitter
                    jitter = (0.1 * backoff)
                    await asyncio.sleep(backoff + jitter)
                    backoff *= 2
                    continue
                # final fallback
                return {
                    "name": "example-pipeline",
                    "stages": [
                        {"name": "load", "type": "source", "params": {"path": "s3://bucket/key"}},
                        {"name": "transform", "type": "map", "params": {"fn": "clean_text"}},
                        {"name": "save", "type": "sink", "params": {"table": "results"}},
                    ],
                }

    async def self_check(self, draft: dict) -> dict:
        method = "self_check"
        provider = self.provider
        if provider != "openai":
            out = {
                "notes": [
                    "Verify `path` exists.",
                    "Validate that `table` is present and accessible.",
                ]
            }
            try:
                LLM_CALLS.labels(method=method, provider=provider, status="ok").inc()
                LLM_LATENCY.labels(method=method, provider=provider).observe(0.0001)
            except Exception:
                pass
            return out
        assert self._client is not None
        system = (
            "You are a code reviewer for DSL pipelines.\n"
            "Return a JSON object with fields: notes (array of strings), risks (array of strings).\n"
            "Only output JSON."
        )
        user = json.dumps({"draft": draft}, ensure_ascii=False)
        attempts = int(getattr(settings, "LLM_RETRIES", 3))
        backoff = 0.5
        for i in range(attempts):
            start = asyncio.get_event_loop().time()
            try:
                resp = await asyncio.wait_for(
                    self._client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system},
                            {"role": "user", "content": user},
                        ],
                        temperature=0.0,
                        response_format={"type": "json_object"},
                    ),
                    timeout=self.timeout,
                )
                content = resp.choices[0].message.content or "{}"
                data = _ensure_json(content)
                if "notes" not in data:
                    data["notes"] = []
                if "risks" not in data:
                    data["risks"] = []
                try:
                    dur = asyncio.get_event_loop().time() - start
                    LLM_CALLS.labels(method=method, provider=provider, status="ok").inc()
                    LLM_LATENCY.labels(method=method, provider=provider).observe(dur)
                except Exception:
                    pass
                return data
            except (asyncio.TimeoutError, OpenAIError):
                try:
                    dur = asyncio.get_event_loop().time() - start
                    LLM_CALLS.labels(method=method, provider=provider, status="error").inc()
                    LLM_LATENCY.labels(method=method, provider=provider).observe(dur)
                except Exception:
                    pass
                if i < attempts - 1:
                    jitter = (0.1 * backoff)
                    await asyncio.sleep(backoff + jitter)
                    backoff *= 2
                    continue
                return {"notes": ["Self-check failed (provider error)."], "risks": []}

    async def summarize(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize a thread. Payload contains {thread_id, flow_id, messages[]}.
        Returns a JSON with keys: summary (string), bullets (array of strings).
        """
        method = "summarize"
        provider = self.provider
        if provider != "openai":
            msgs = payload.get("messages", []) or []
            count = len(msgs)
            last = msgs[-1]["content"] if msgs else {}
            out = {
                "summary": f"Короткий підсумок обговорення: {count} повідомлень.",
                "bullets": [
                    "Огляд цілей користувача",
                    "Основні кроки, які було обговорено",
                ],
                "last_hint": last,
            }
            try:
                LLM_CALLS.labels(method=method, provider=provider, status="ok").inc()
                LLM_LATENCY.labels(method=method, provider=provider).observe(0.0001)
            except Exception:
                pass
            return out
        assert self._client is not None
        system = (
            "You are a helpful assistant that summarizes chat threads for engineers.\n"
            "Return a JSON object with fields: summary (string, concise UA), bullets (array of 2-5 concise UA strings).\n"
            "Only output JSON."
        )
        user = json.dumps({"thread": payload}, ensure_ascii=False)
        attempts = int(getattr(settings, "LLM_RETRIES", 3))
        backoff = 0.5
        for i in range(attempts):
            start = asyncio.get_event_loop().time()
            try:
                resp = await asyncio.wait_for(
                    self._client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system},
                            {"role": "user", "content": user},
                        ],
                        temperature=0.2,
                        response_format={"type": "json_object"},
                    ),
                    timeout=self.timeout,
                )
                content = resp.choices[0].message.content or "{}"
                data = _ensure_json(content)
                if "summary" not in data:
                    data["summary"] = ""
                if "bullets" not in data:
                    data["bullets"] = []
                try:
                    dur = asyncio.get_event_loop().time() - start
                    LLM_CALLS.labels(method=method, provider=provider, status="ok").inc()
                    LLM_LATENCY.labels(method=method, provider=provider).observe(dur)
                except Exception:
                    pass
                return data
            except (asyncio.TimeoutError, OpenAIError):
                try:
                    dur = asyncio.get_event_loop().time() - start
                    LLM_CALLS.labels(method=method, provider=provider, status="error").inc()
                    LLM_LATENCY.labels(method=method, provider=provider).observe(dur)
                except Exception:
                    pass
                if i < attempts - 1:
                    jitter = (0.1 * backoff)
                    await asyncio.sleep(backoff + jitter)
                    backoff *= 2
                    continue
                return {
                    "summary": "Короткий підсумок обговорення (LLM timeout).",
                    "bullets": [],
                }
