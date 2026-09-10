"""Chroma-backed implementation of the VectorStore Protocol.

Chroma is an embedded vector DB — no server required. It persists to a
directory on disk (see settings.chroma_persist_dir), so restarts don't
lose indexed papers.

Distance metric: cosine. Since our embeddings are unit-normalized, that's
equivalent to dot product but Chroma handles the math either way.
"""
from __future__ import annotations

import logging
from typing import Any

from app.config import get_settings
from app.vectorstore.base import SearchHit, VectorRecord

logger = logging.getLogger(__name__)


class ChromaStore:
    def __init__(self, persist_dir: str, collection_name: str) -> None:
        # Lazy import — keeps startup fast for code paths that never hit the store.
        import chromadb

        self._client = chromadb.PersistentClient(path=persist_dir)
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "chroma store ready dir=%s collection=%s count=%d",
            persist_dir,
            collection_name,
            self._collection.count(),
        )

    def add(self, records: list[VectorRecord]) -> None:
        if not records:
            return
        self._collection.add(
            ids=[r.id for r in records],
            embeddings=[r.embedding for r in records],
            documents=[r.text for r in records],
            metadatas=[_sanitize_metadata(r.metadata) for r in records],
        )

    def similarity_search(
        self, query_embedding: list[float], k: int = 5
    ) -> list[SearchHit]:
        result = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
        )
        ids = result.get("ids", [[]])[0]
        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        # Chroma returns *distances*; convert to a similarity score in [0, 1].
        # For cosine distance, similarity = 1 - distance.
        distances = result.get("distances", [[]])[0]

        hits: list[SearchHit] = []
        for id_, doc, meta, dist in zip(ids, docs, metas, distances):
            hits.append(
                SearchHit(
                    id=id_,
                    text=doc or "",
                    metadata=meta or {},
                    score=float(1.0 - dist),
                )
            )
        return hits

    def existing_pmids(self, pmids: list[str]) -> set[str]:
        if not pmids:
            return set()
        # Chroma `get` with a `where` filter is the cheapest way to check.
        result = self._collection.get(
            where={"pmid": {"$in": pmids}},
            include=["metadatas"],
            limit=100_000,
        )
        metas = result.get("metadatas") or []
        return {m["pmid"] for m in metas if m and "pmid" in m}

    def count(self) -> int:
        return int(self._collection.count())


def _sanitize_metadata(meta: dict[str, Any]) -> dict[str, Any]:
    """Chroma only accepts scalar values in metadata (str, int, float, bool).

    Lists (e.g. authors) get joined; None becomes "".
    """
    out: dict[str, Any] = {}
    for k, v in meta.items():
        if v is None:
            out[k] = ""
        elif isinstance(v, (str, int, float, bool)):
            out[k] = v
        elif isinstance(v, list):
            out[k] = "; ".join(str(x) for x in v)
        else:
            out[k] = str(v)
    return out


_singleton: ChromaStore | None = None


def get_vector_store() -> ChromaStore:
    """Cached accessor — one store per process.

    We don't use lru_cache here so tests can reset the singleton easily.
    """
    global _singleton
    if _singleton is None:
        settings = get_settings()
        _singleton = ChromaStore(
            persist_dir=settings.chroma_persist_dir,
            collection_name=settings.chroma_collection,
        )
    return _singleton


def reset_vector_store() -> None:
    """For tests: forget the cached instance."""
    global _singleton
    _singleton = None
