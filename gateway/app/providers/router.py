"""Provider selection. Returns the configured BaseLLMProvider.

All four providers are implemented; choose with ``LLM_PROVIDER``. The httpx-based
providers reuse the gateway's shared connection-pooled client.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.config import LLMProvider, Settings
from app.providers.base import BaseLLMProvider
from app.providers.claude import ClaudeProvider
from app.providers.gemini import GeminiProvider
from app.providers.ollama import OllamaProvider
from app.providers.openai import OpenAIProvider

if TYPE_CHECKING:
    import httpx


def get_provider(settings: Settings, http_client: "httpx.AsyncClient | None" = None) -> BaseLLMProvider:
    p = settings.llm_provider
    if p is LLMProvider.gemini:
        return GeminiProvider(settings.gemini_api_key, settings.gemini_model)
    if p is LLMProvider.openai:
        return OpenAIProvider(settings.openai_api_key, http_client)
    if p is LLMProvider.claude:
        return ClaudeProvider(settings.anthropic_api_key, http_client)
    if p is LLMProvider.ollama:
        return OllamaProvider(http_client, settings.ollama_base_url)
    raise NotImplementedError(f"unknown provider: {p}")
