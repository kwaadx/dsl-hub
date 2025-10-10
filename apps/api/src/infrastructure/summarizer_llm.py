from __future__ import annotations

from typing import List, Dict, Any, Optional
from ..core.ports import SummarizerPort
from ..infrastructure.llm_openai import OpenAILLM

SYS_SUMMARIZE_THREAD = "You are a helpful assistant that writes concise summaries. Output JSON with keys: summary (string), bullets (array of strings). Be brief but cover key facts."
SYS_SUMMARIZE_FLOW = "You are a helpful assistant that writes a cohesive summary across multiple thread summaries. Output JSON with keys: summary (string), bullets (array of strings))."

class LLMSummarizer(SummarizerPort):
    def __init__(self, llm: OpenAILLM | None = None):
        self.llm = llm or OpenAILLM()

    async def summarize_thread(self, messages: List[Dict[str, Any]], *, kind: str = "short") -> Dict[str, Any]:
        user = {"role": "user", "content": f"Summarize the conversation. Kind: {kind}. Return ONLY JSON."}
        sys = {"role": "system", "content": SYS_SUMMARIZE_THREAD}
        res = await self.llm.chat([sys] + messages + [user])
        try:
            content = res["choices"][0]["message"]["content"]
        except Exception:
            content = "{}"
        import json as _json
        try:
            data = _json.loads(content)
        except Exception:
            data = {"summary": content, "bullets": []}
        return {"kind": kind, "content": data}

    async def summarize_flow(self, thread_summaries: List[Dict[str, Any]]) -> Dict[str, Any]:
        sys = {"role": "system", "content": SYS_SUMMARIZE_FLOW}
        summaries_str = "\n\n".join([f"- {s.get('kind','short')}: {s.get('content',{}).get('summary','')}" for s in thread_summaries])
        user = {"role": "user", "content": f"Combine the following points into a cohesive summary. Return ONLY JSON.\n{summaries_str}"}
        res = await self.llm.chat([sys, user])
        try:
            content = res["choices"][0]["message"]["content"]
        except Exception:
            content = "{}"
        import json as _json
        try:
            data = _json.loads(content)
        except Exception:
            data = {"summary": content, "bullets": []}
        return {"content": data}