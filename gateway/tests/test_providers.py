"""Phase 6 — provider response parsing (no network; httpx MockTransport) and
router selection."""

from __future__ import annotations

import httpx
import pytest

from app.config import LLMProvider, Settings
from app.providers.claude import ClaudeProvider
from app.providers.gemini import GeminiProvider
from app.providers.ollama import OllamaProvider
from app.providers.openai import OpenAIProvider
from app.providers.router import get_provider


def _client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


async def test_openai_parsing():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer k"
        return httpx.Response(200, json={"choices": [{"message": {"content": "hello"}}]})

    async with _client(handler) as c:
        p = OpenAIProvider("k", c)
        assert await p.complete("hi") == "hello"


async def test_openai_requires_key():
    async with _client(lambda r: httpx.Response(200)) as c:
        with pytest.raises(RuntimeError):
            await OpenAIProvider(None, c).complete("hi")


async def test_claude_parsing():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-api-key"] == "k"
        return httpx.Response(
            200, json={"content": [{"type": "text", "text": "hi "}, {"type": "text", "text": "there"}]}
        )

    async with _client(handler) as c:
        assert await ClaudeProvider("k", c).complete("x") == "hi there"


async def test_ollama_parsing():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/generate"
        return httpx.Response(200, json={"response": "local answer"})

    async with _client(handler) as c:
        assert await OllamaProvider(c, "http://h:11434").complete("x") == "local answer"


def test_router_selects_each_provider():
    base = {"gemini_api_key": "g", "openai_api_key": "o", "anthropic_api_key": "a"}
    assert isinstance(get_provider(Settings(llm_provider=LLMProvider.gemini, **base)), GeminiProvider)
    assert isinstance(get_provider(Settings(llm_provider=LLMProvider.openai, **base)), OpenAIProvider)
    assert isinstance(get_provider(Settings(llm_provider=LLMProvider.claude, **base)), ClaudeProvider)
    assert isinstance(get_provider(Settings(llm_provider=LLMProvider.ollama, **base)), OllamaProvider)
