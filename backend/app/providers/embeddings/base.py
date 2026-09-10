"""Abstract embedding provider.

The rest of the app should depend on this Protocol, not on any concrete impl.
That way we can swap sentence-transformers ↔ OpenAI ↔ mock without touching
services or routes.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Return dense float vectors for text.

    `embed_documents` and `embed_query` are split because some models
    (e.g. instruction-tuned ones) use different prefixes for docs vs queries.
    Even when they're identical, keeping them separate documents intent.
    """

    dimension: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        ...

    def embed_query(self, text: str) -> list[float]:
        ...
