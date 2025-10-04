"""
LLM abstraction with pluggable providers.
Default: mock generator. If settings.LLM_PROVIDER == "openai", uses OpenAI Chat Completions.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any, Optional, Dict, Callable

from ..config import settings
from ..metrics import LLM_CALLS, LLM_LATENCY

try:
    # Import lazily; only required when provider is openai
    from openai import AsyncOpenAI
    from openai import OpenAIError  # type: ignore
except ImportError:  # pragma: no cover
    AsyncOpenAI = None  # type: ignore
    OpenAIError = Exception  # type: ignore


def _default_pipeline() -> Dict[str, Any]:
    """Return a fresh default pipeline payload."""
    return {
        "name": "example-pipeline",
        "stages": [
            {"name": "load", "type": "source", "params": {"path": "s3://bucket/key"}},
            {"name": "transform", "type": "map", "params": {"fn": "clean_text"}},
            {"name": "save", "type": "sink", "params": {"table": "results"}},
        ],
    }


def _record_metrics(method: str, provider: str, status: str, duration: Optional[float] = None) -> None:
    """Best-effort metrics recording with narrow exception handling."""
    try:
        LLM_CALLS.labels(method=method, provider=provider, status=status).inc()
        if duration is None:
            # use a tiny positive number to avoid zero-value bin artifacts
            LLM_LATENCY.labels(method=method, provider=provider).observe(0.0001)
        else:
            LLM_LATENCY.labels(method=method, provider=provider).observe(duration)
    except (ValueError, TypeError, RuntimeError):
        # Never let metrics break user flow
        return


def _ensure_json(text: str) -> Dict[str, Any]:
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
        return _default_pipeline()


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

    async def _chat_json_retry(
        self,
        method: str,
        system: str,
        user: str,
        temperature: float,
        finalize: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]],
        fallback: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Call OpenAI Chat Completions with JSON response_format, retries, and metrics.
        Assumes provider == 'openai'. The finalize callback can normalize the parsed JSON.
        """
        provider = self.provider
        assert self._client is not None
        attempts = max(1, int(getattr(settings, "LLM_RETRIES", 3)))
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
                        temperature=temperature,
                        response_format={"type": "json_object"},
                    ),
                    timeout=self.timeout,
                )
                content = resp.choices[0].message.content or "{}"
                data = _ensure_json(content)
                if finalize is not None:
                    try:
                        data = finalize(data)
                    except (TypeError, ValueError):
                        # if finalize fails, proceed with parsed data
                        pass
                dur = asyncio.get_event_loop().time() - start
                _record_metrics(method, provider, "ok", dur)
                return data
            except (asyncio.TimeoutError, OpenAIError):
                dur = asyncio.get_event_loop().time() - start
                _record_metrics(method, provider, "error", dur)
                if i < attempts - 1:
                    jitter = (0.1 * backoff)
                    await asyncio.sleep(backoff + jitter)
                    backoff *= 2
                    continue
                return fallback
        # Safety fallback
        return fallback

    async def generate_pipeline(self, context: Dict[str, Any], user_message: Dict[str, Any]) -> Dict[str, Any]:
        method = "generate_pipeline"
        provider = self.provider
        if provider != "openai":
            # mock path
            out = _default_pipeline()
            _record_metrics(method, provider, "ok", None)
            return out
        # OpenAI provider with retry/backoff (refactored)
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
        return await self._chat_json_retry(
            method=method,
            system=system,
            user=user,
            temperature=0.2,
            finalize=None,
            fallback=_default_pipeline(),
        )

    async def self_check(self, draft: Dict[str, Any]) -> Dict[str, Any]:
        method = "self_check"
        provider = self.provider
        if provider != "openai":
            out = {
                "notes": [
                    "Verify `path` exists.",
                    "Validate that `table` is present and accessible.",
                ],
                "risks": [],
            }
            _record_metrics(method, provider, "ok", None)
            return out
        assert self._client is not None
        system = (
            "You are a code reviewer for DSL pipelines.\n"
            "Return a JSON object with fields: notes (array of strings), risks (array of strings).\n"
            "Only output JSON."
        )
        user = json.dumps({"draft": draft}, ensure_ascii=False)
        def _finalize_sc(data: Dict[str, Any]) -> Dict[str, Any]:
            if "notes" not in data:
                data["notes"] = []
            if "risks" not in data:
                data["risks"] = []
            return data
        return await self._chat_json_retry(
            method=method,
            system=system,
            user=user,
            temperature=0.0,
            finalize=_finalize_sc,
            fallback={"notes": ["Self-check failed (provider error)."], "risks": []},
        )

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
            out = dict(
                summary=f"Brief discussion summary: {count} messages.",
                bullets=[
                    "Overview of user goals",
                    "Key steps discussed",
                ],
                last_hint=last,
            )
            _record_metrics(method, provider, "ok", None)
            return out
        assert self._client is not None
        system = (
            "You are a helpful assistant that summarizes chat threads for engineers.\n"
            "Return a JSON object with fields: summary (string, concise English), bullets (array of 2-5 concise English strings).\n"
            "Only output JSON."
        )
        user = json.dumps({"thread": payload}, ensure_ascii=False)
        def _finalize_sum(data: Dict[str, Any]) -> Dict[str, Any]:
            if "summary" not in data:
                data["summary"] = ""
            if "bullets" not in data:
                data["bullets"] = []
            return data
        return await self._chat_json_retry(
            method=method,
            system=system,
            user=user,
            temperature=0.2,
            finalize=_finalize_sum,
            fallback=dict(
                summary="Brief discussion summary (LLM timeout).",
                bullets=[],
            ),
        )
