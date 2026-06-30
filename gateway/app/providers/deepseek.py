"""DeepSeek provider — OpenAI-compatible Chat Completions API."""

from __future__ import annotations

import httpx

from app.providers.openai import OpenAIProvider


class DeepSeekProvider(OpenAIProvider):
    name = "deepseek"
    URL = "https://api.deepseek.com/chat/completions"
    KEY_NAME = "DEEPSEEK_API_KEY"

    def __init__(
        self, api_key: str | None, client: httpx.AsyncClient, model: str = "deepseek-chat"
    ) -> None:
        super().__init__(api_key, client, model)
