from __future__ import annotations

from typing import List, Dict, Any, Optional
import httpx
import os

class OpenAILLM:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("API_OPENAI_API_KEY")
        self.base_url = (base_url or os.getenv("API_OPENAI_BASE_URL") or "https://api.openai.com").rstrip("/")
        self.model = model or os.getenv("API_OPENAI_MODEL") or "gpt-4o-mini"
    async def chat(self, messages: List[Dict[str, Any]], *, timeout: int | None = None) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        url = f"{self.base_url}/v1/chat/completions"
        payload = {"model": self.model, "messages": messages, "temperature": 0.2}
        async with httpx.AsyncClient(timeout=timeout or 30) as client:
            r = await client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            return r.json()