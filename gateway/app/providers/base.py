"""Provider-agnostic LLM interface.

Every provider implements the same contract so the gateway can switch between
Gemini / OpenAI / Claude / Ollama by configuration alone. Streaming (``stream``)
is added in Phase 7; for now providers must implement ``complete``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class BaseLLMProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def complete(self, prompt: str, *, model: str | None = None) -> str:
        """Return the full completion for a single prompt."""

    async def stream(self, prompt: str, *, model: str | None = None) -> AsyncIterator[str]:
        """Yield completion chunks. Default: emit the full completion once.

        Providers with native streaming override this in Phase 7.
        """
        yield await self.complete(prompt, model=model)
