"""Abstract reranker.

A reranker scores query-passage pairs *together* (cross-encoder), which is
more accurate than the vector similarity used at retrieval time but too
slow to run on the whole corpus. The usual recipe:

    vector search top-N (fast, coarse)  →  rerank to top-K (slow, precise)
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Reranker(Protocol):
    def score(self, query: str, passages: list[str]) -> list[float]:
        """Return a relevance score per passage. Higher = more relevant."""
        ...
