"""Anthropic Claude (Messages API) provider."""

from __future__ import annotations

import httpx

from app.providers.base import BaseLLMProvider


class ClaudeProvider(BaseLLMProvider):
    name = "claude"
    URL = "https://api.anthropic.com/v1/messages"
    VERSION = "2023-06-01"

    def __init__(
        self,
        api_key: str | None,
        client: httpx.AsyncClient,
        model: str = "claude-opus-4-8",
        max_tokens: int = 1024,
    ) -> None:
        self._api_key = api_key
        self._client = client
        self._model = model
        self._max_tokens = max_tokens

    async def complete(self, prompt: str, *, model: str | None = None) -> str:
        if not self._api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not configured")
        resp = await self._client.post(
            self.URL,
            headers={"x-api-key": self._api_key, "anthropic-version": self.VERSION},
            json={
                "model": model or self._model,
                "max_tokens": self._max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        resp.raise_for_status()
        return "".join(
            block.get("text", "")
            for block in resp.json().get("content", [])
            if block.get("type") == "text"
        )
