"""Provider selection + registry.

All providers are implemented; the active one is chosen by config, and the
gateway can switch per-request (the frontend exposes a selector). The
httpx-based providers reuse the gateway's shared connection-pooled client.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.config import LLMProvider, Settings
from app.providers.base import BaseLLMProvider
from app.providers.claude import ClaudeProvider
from app.providers.deepseek import DeepSeekProvider
from app.providers.gemini import GeminiProvider
from app.providers.ollama import OllamaProvider
from app.providers.openai import OpenAIProvider

if TYPE_CHECKING:
    import httpx


def _build(name: LLMProvider, settings: Settings, http_client) -> BaseLLMProvider:
    if name is LLMProvider.gemini:
        return GeminiProvider(settings.gemini_api_key, settings.gemini_model)
    if name is LLMProvider.openai:
        return OpenAIProvider(settings.openai_api_key, http_client)
    if name is LLMProvider.claude:
        return ClaudeProvider(settings.anthropic_api_key, http_client, settings.anthropic_model)
    if name is LLMProvider.ollama:
        return OllamaProvider(http_client, settings.ollama_base_url)
    if name is LLMProvider.deepseek:
        return DeepSeekProvider(settings.deepseek_api_key, http_client)
    raise NotImplementedError(f"unknown provider: {name}")


def get_provider(settings: Settings, http_client: "httpx.AsyncClient | None" = None) -> BaseLLMProvider:
    """The default provider (from LLM_PROVIDER)."""
    return _build(settings.llm_provider, settings, http_client)


def build_provider_registry(
    settings: Settings, http_client: "httpx.AsyncClient | None" = None
) -> dict[str, BaseLLMProvider]:
    """Providers exposed for per-request selection.

    Only the configured default provider is offered to clients (currently Gemini,
    which has a free tier). The other provider implementations remain available
    via ``get_provider`` / ``LLM_PROVIDER`` — the gateway stays provider-agnostic
    — but aren't surfaced in the UI so users don't hit unfunded-account errors.
    """
    provider = get_provider(settings, http_client)
    return {provider.name: provider}
