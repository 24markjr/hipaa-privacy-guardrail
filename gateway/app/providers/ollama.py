"""Ollama (local LLM runtime) provider."""

from __future__ import annotations

import httpx

from app.providers.base import BaseLLMProvider


class OllamaProvider(BaseLLMProvider):
    name = "ollama"

    def __init__(
        self,
        client: httpx.AsyncClient,
        base_url: str = "http://localhost:11434",
        model: str = "llama3",
    ) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")
        self._model = model

    async def complete(self, prompt: str, *, model: str | None = None) -> str:
        resp = await self._client.post(
            f"{self._base_url}/api/generate",
            json={"model": model or self._model, "prompt": prompt, "stream": False},
        )
        resp.raise_for_status()
        return resp.json().get("response", "")
