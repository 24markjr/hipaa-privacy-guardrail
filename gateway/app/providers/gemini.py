"""Google Gemini provider — ports the MVP's aiService behaviour.

The google-genai SDK call is synchronous, so it's run in a worker thread to
avoid blocking the event loop. The client is created lazily on first use so the
app can boot (and run with other providers) without a Gemini key configured.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from app.providers.base import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):
    name = "gemini"

    def __init__(self, api_key: str | None, model: str = "gemini-2.5-flash") -> None:
        self._api_key = api_key
        self._model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            if not self._api_key:
                raise RuntimeError("GEMINI_API_KEY is not configured")
            from google import genai  # lazy import

            self._client = genai.Client(api_key=self._api_key)
        return self._client

    def _complete_sync(self, prompt: str, model: str) -> str:
        client = self._get_client()
        resp = client.models.generate_content(model=model, contents=prompt)
        return resp.text or ""

    async def complete(self, prompt: str, *, model: str | None = None) -> str:
        return await asyncio.to_thread(self._complete_sync, prompt, model or self._model)

    async def stream(self, prompt: str, *, model: str | None = None) -> AsyncIterator[str]:
        """Native token streaming. The SDK's stream is a sync generator, so we
        drain it in a worker thread and hand chunks to the event loop via a
        thread-safe queue."""
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue()
        done = object()
        mdl = model or self._model

        def produce() -> None:
            try:
                client = self._get_client()
                for chunk in client.models.generate_content_stream(model=mdl, contents=prompt):
                    loop.call_soon_threadsafe(queue.put_nowait, chunk.text or "")
            except Exception as exc:  # propagate to the consumer
                loop.call_soon_threadsafe(queue.put_nowait, exc)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, done)

        fut = loop.run_in_executor(None, produce)
        try:
            while True:
                item = await queue.get()
                if item is done:
                    break
                if isinstance(item, Exception):
                    raise item
                yield item
        finally:
            await fut
