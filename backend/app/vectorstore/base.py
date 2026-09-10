"""Vector store abstraction.

The rest of the app talks to `VectorStore` — never directly to Chroma or pgvector.
Swapping implementations later means writing a new class that satisfies this
Protocol; no callers change.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class VectorRecord:
    """A single chunk we want to store or that came back from a search."""
    id: str
    text: str
    embedding: list[float] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchHit:
    id: str
    text: str
    metadata: dict[str, Any]
    score: float  # higher = more similar (cosine similarity)


@runtime_checkable
class VectorStore(Protocol):
    def add(self, records: list[VectorRecord]) -> None: ...
    def similarity_search(
        self, query_embedding: list[float], k: int = 5
    ) -> list[SearchHit]: ...
    def existing_pmids(self, pmids: list[str]) -> set[str]:
        """Return the subset of the given PMIDs that already have chunks stored."""
        ...
    def count(self) -> int: ...
