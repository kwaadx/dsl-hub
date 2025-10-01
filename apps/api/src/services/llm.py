"""
LLM abstraction with pluggable providers.
Default: mock generator. If settings.LLM_PROVIDER == "openai", uses OpenAI Chat Completions.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any, Optional

from ..config import settings

try:
    # Import lazily; only required when provider is openai
    from openai import AsyncOpenAI
except Exception:  # pragma: no cover
    AsyncOpenAI = None  # type: ignore


def _ensure_json(text: str) -> dict:
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
    except Exception:
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
        if self.provider != "openai":
            # return a tiny valid draft based on schema expectations (placeholder)
            return {
                "name": "example-pipeline",
                "stages": [
                    {"name": "load", "type": "source", "params": {"path": "s3://bucket/key"}},
                    {"name": "transform", "type": "map", "params": {"fn": "clean_text"}},
                    {"name": "save", "type": "sink", "params": {"table": "results"}},
                ],
            }
        # OpenAI provider
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
        try:
            # Use response_format to encourage JSON
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
            return _ensure_json(content)
        except Exception:
            # graceful fallback
            return {
                "name": "example-pipeline",
                "stages": [
                    {"name": "load", "type": "source", "params": {"path": "s3://bucket/key"}},
                    {"name": "transform", "type": "map", "params": {"fn": "clean_text"}},
                    {"name": "save", "type": "sink", "params": {"table": "results"}},
                ],
            }

    async def self_check(self, draft: dict) -> dict:
        if self.provider != "openai":
            return {
                "notes": [
                    "Verify `path` exists.",
                    "Validate that `table` is present and accessible.",
                ]
            }
        assert self._client is not None
        system = (
            "You are a code reviewer for DSL pipelines.\n"
            "Return a JSON object with fields: notes (array of strings), risks (array of strings).\n"
            "Only output JSON."
        )
        user = json.dumps({"draft": draft}, ensure_ascii=False)
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
            # ensure shape
            if "notes" not in data:
                data["notes"] = []
            if "risks" not in data:
                data["risks"] = []
            return data
        except Exception:
            return {"notes": ["Self-check failed (provider error)."], "risks": []}
