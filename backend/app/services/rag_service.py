"""RAG orchestration: embed question → retrieve → prompt → generate → cite.

Citation contract:
  - We deduplicate retrieved chunks by pmid (one paper -> one citation number),
    keeping the highest-scoring chunk per paper as the representative snippet.
  - We hand the LLM a numbered list [1..N] of those unique papers.
  - The `sources` we return to the frontend uses the same numbering, so
    "[2]" in the model's answer always maps to `sources[1]`.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import AsyncIterator


_CITATION_RE = re.compile(r"\[(\d+)\]")


def find_invalid_citations(answer: str, source_count: int) -> list[int]:
    """Return citation numbers in `answer` that don't map to a real source.

    A well-behaved model only uses [1]..[source_count]. Any [N] with N>count
    or N<1 is a hallucination — we surface it so the caller can log/flag.
    """
    invalid: list[int] = []
    for match in _CITATION_RE.finditer(answer):
        n = int(match.group(1))
        if n < 1 or n > source_count:
            invalid.append(n)
    return invalid

from app.models.schemas import Source
from app.prompts.rag_prompt import ContextChunk, build_rag_prompt
from app.services.library_service import _year
from app.providers.embeddings.sentence_transformers_provider import (
    get_embedding_provider,
)
from app.providers.llm.ollama_provider import get_llm_provider
from app.providers.reranker.cross_encoder import get_reranker
from app.config import get_settings
from app.vectorstore.chroma_store import get_vector_store

logger = logging.getLogger(__name__)


@dataclass
class RAGAnswer:
    answer: str
    sources: list[Source]


class RAGService:
    def __init__(
        self,
        vector_store=None,
        embedder=None,
        llm=None,
        reranker=None,
    ) -> None:
        self._store = vector_store or get_vector_store()
        self._embedder = embedder or get_embedding_provider()
        self._llm = llm or get_llm_provider()
        # reranker=None is the "not injected" sentinel — fall back to the
        # config-driven factory (which may itself return None when disabled).
        self._reranker = reranker if reranker is not None else get_reranker()
        self._settings = get_settings()

    def _rerank(self, question: str, hits):
        """Rescore hits with the cross-encoder if one is configured.

        Overwrites `.score` in place so downstream dedup keeps working
        exactly as before — it always picks max-score per pmid.
        """
        if not self._reranker or not hits:
            return hits
        passages = [h.text for h in hits]
        scores = self._reranker.score(question, passages)
        for h, s in zip(hits, scores):
            h.score = float(s)
        hits.sort(key=lambda h: h.score, reverse=True)
        logger.info("rag.rerank rescored=%d", len(hits))
        return hits

    async def ask(
        self,
        question: str,
        top_k: int = 6,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> RAGAnswer:
        # 1. Retrieve.
        q_vec = self._embedder.embed_query(question)
        pool = max(top_k * 4, self._settings.reranker_candidate_pool)
        hits = self._store.similarity_search(q_vec, k=pool)
        hits = _filter_by_year(hits, year_from, year_to)
        hits = self._rerank(question, hits)
        if not hits:
            return RAGAnswer(
                answer=(
                    "I couldn't find any papers in the index that address that question. "
                    "Try ingesting more papers first, then ask again."
                ),
                sources=[],
            )

        # 2. Dedup by pmid — one citation per paper.
        best_by_pmid: dict[str, tuple[float, str, dict]] = {}
        for h in hits:
            pmid = h.metadata.get("pmid")
            if not pmid:
                continue
            if pmid not in best_by_pmid or h.score > best_by_pmid[pmid][0]:
                best_by_pmid[pmid] = (h.score, h.text, h.metadata)

        # Rank the unique papers by their best chunk score, keep top_k.
        ranked = sorted(best_by_pmid.items(), key=lambda kv: kv[1][0], reverse=True)[:top_k]

        # 3. Build numbered SOURCE blocks + parallel Source[] for the response.
        context_chunks: list[ContextChunk] = []
        sources: list[Source] = []
        for i, (pmid, (score, text, meta)) in enumerate(ranked, start=1):
            context_chunks.append(
                ContextChunk(
                    citation_number=i,
                    pmid=pmid,
                    title=meta.get("title", ""),
                    text=text,
                )
            )
            sources.append(
                Source(
                    pmid=pmid,
                    title=meta.get("title", ""),
                    journal=meta.get("journal", "") or "",
                    publication_date=meta.get("publication_date", "") or "",
                    pubmed_url=meta.get("pubmed_url")
                    or f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    relevance_score=round(score, 4),
                )
            )

        # 4. Generate.
        prompt = build_rag_prompt(question, context_chunks)
        answer = await self._llm.generate(prompt)

        # 5. Sanity-check the citations the model produced.
        invalid = find_invalid_citations(answer, source_count=len(sources))
        if invalid:
            logger.warning(
                "rag.ask hallucinated citations: %s (had %d sources)",
                sorted(set(invalid)),
                len(sources),
            )

        logger.info(
            "rag.ask top_k=%d sources=%d answer_chars=%d invalid_citations=%d",
            top_k,
            len(sources),
            len(answer),
            len(invalid),
        )
        return RAGAnswer(answer=answer, sources=sources)


    async def ask_stream(
        self,
        question: str,
        top_k: int = 6,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> AsyncIterator[str]:
        """Yield newline-delimited JSON events for the /ask/stream endpoint.

        Event shapes:
          {"type":"sources","sources":[...]}   # sent first
          {"type":"token","content":"..."}     # sent many times
          {"type":"done"}                       # sent last
        """
        q_vec = self._embedder.embed_query(question)
        pool = max(top_k * 4, self._settings.reranker_candidate_pool)
        hits = self._store.similarity_search(q_vec, k=pool)
        hits = _filter_by_year(hits, year_from, year_to)
        hits = self._rerank(question, hits)

        if not hits:
            msg = (
                "I couldn't find any papers in the index that address that question. "
                "Try ingesting more papers first, then ask again."
            )
            yield _ndjson({"type": "sources", "sources": []})
            yield _ndjson({"type": "token", "content": msg})
            yield _ndjson({"type": "done"})
            return

        # Dedup by pmid — same rules as `ask()`.
        best_by_pmid: dict[str, tuple[float, str, dict]] = {}
        for h in hits:
            pmid = h.metadata.get("pmid")
            if not pmid:
                continue
            if pmid not in best_by_pmid or h.score > best_by_pmid[pmid][0]:
                best_by_pmid[pmid] = (h.score, h.text, h.metadata)
        ranked = sorted(best_by_pmid.items(), key=lambda kv: kv[1][0], reverse=True)[:top_k]

        context_chunks: list[ContextChunk] = []
        sources: list[Source] = []
        for i, (pmid, (score, text, meta)) in enumerate(ranked, start=1):
            context_chunks.append(
                ContextChunk(
                    citation_number=i,
                    pmid=pmid,
                    title=meta.get("title", ""),
                    text=text,
                )
            )
            sources.append(
                Source(
                    pmid=pmid,
                    title=meta.get("title", ""),
                    journal=meta.get("journal", "") or "",
                    publication_date=meta.get("publication_date", "") or "",
                    pubmed_url=meta.get("pubmed_url")
                    or f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    relevance_score=round(score, 4),
                )
            )

        yield _ndjson({"type": "sources", "sources": [s.model_dump() for s in sources]})

        prompt = build_rag_prompt(question, context_chunks)
        full_answer_parts: list[str] = []
        async for chunk in self._llm.stream(prompt):
            full_answer_parts.append(chunk)
            yield _ndjson({"type": "token", "content": chunk})

        # After streaming, run the same hallucination check as ask() and log.
        full = "".join(full_answer_parts)
        invalid = find_invalid_citations(full, source_count=len(sources))
        if invalid:
            logger.warning(
                "rag.ask_stream hallucinated citations: %s (had %d sources)",
                sorted(set(invalid)),
                len(sources),
            )

        logger.info(
            "rag.ask_stream top_k=%d sources=%d answer_chars=%d invalid_citations=%d",
            top_k,
            len(sources),
            len(full),
            len(invalid),
        )
        yield _ndjson({"type": "done"})


def _ndjson(obj: dict) -> str:
    return json.dumps(obj, separators=(",", ":")) + "\n"


def _filter_by_year(hits, year_from: int | None, year_to: int | None):
    if year_from is None and year_to is None:
        return hits
    lo = year_from or 1900
    hi = year_to or 2100
    out = []
    for h in hits:
        y = _year(h.metadata.get("publication_date") or "")
        if y is None:
            # Keep chunks with unknown dates only if no filter is set at all.
            continue
        if lo <= y <= hi:
            out.append(h)
    return out


def get_rag_service() -> RAGService:
    return RAGService()
