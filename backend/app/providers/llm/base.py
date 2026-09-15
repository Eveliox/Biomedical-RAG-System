"""Abstract LLM provider.

Same idea as EmbeddingProvider: services depend on this Protocol, not on
Ollama or OpenAI directly, so we can swap backends by changing one factory.
"""
from __future__ import annotations

from typing import AsyncIterator, Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    async def generate(self, prompt: str, *, temperature: float = 0.1) -> str:
        """Return the model's completion for the given prompt."""
        ...

    def stream(
        self, prompt: str, *, temperature: float = 0.1
    ) -> AsyncIterator[str]:
        """Yield the model's completion token-by-token (or chunk-by-chunk)."""
        ...
