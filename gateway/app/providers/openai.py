"""OpenAI Chat Completions provider (uses the gateway's shared httpx client)."""

from __future__ import annotations

import httpx

from app.providers.base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    name = "openai"
    URL = "https://api.openai.com/v1/chat/completions"

    def __init__(
        self, api_key: str | None, client: httpx.AsyncClient, model: str = "gpt-4o-mini"
    ) -> None:
        self._api_key = api_key
        self._client = client
        self._model = model

    async def complete(self, prompt: str, *, model: str | None = None) -> str:
        if not self._api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        resp = await self._client.post(
            self.URL,
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={
                "model": model or self._model,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
