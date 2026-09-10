"""RAG orchestration: embed question → retrieve → prompt → generate → cite.

Citation contract:
  - We deduplicate retrieved chunks by pmid (one paper -> one citation number),
    keeping the highest-scoring chunk per paper as the representative snippet.
  - We hand the LLM a numbered list [1..N] of those unique papers.
  - The `sources` we return to the frontend uses the same numbering, so
    "[2]" in the model's answer always maps to `sources[1]`.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from app.models.schemas import Source
from app.prompts.rag_prompt import ContextChunk, build_rag_prompt
from app.providers.embeddings.sentence_transformers_provider import (
    get_embedding_provider,
)
from app.providers.llm.ollama_provider import get_llm_provider
from app.vectorstore.chroma_store import get_vector_store

logger = logging.getLogger(__name__)


@dataclass
class RAGAnswer:
    answer: str
    sources: list[Source]


class RAGService:
    def __init__(self, vector_store=None, embedder=None, llm=None) -> None:
        self._store = vector_store or get_vector_store()
        self._embedder = embedder or get_embedding_provider()
        self._llm = llm or get_llm_provider()

    async def ask(self, question: str, top_k: int = 6) -> RAGAnswer:
        # 1. Retrieve.
        q_vec = self._embedder.embed_query(question)
        # Ask for more than top_k so we have headroom after dedup by paper.
        hits = self._store.similarity_search(q_vec, k=top_k * 2)
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

        logger.info(
            "rag.ask top_k=%d sources=%d answer_chars=%d",
            top_k,
            len(sources),
            len(answer),
        )
        return RAGAnswer(answer=answer, sources=sources)


def get_rag_service() -> RAGService:
    return RAGService()
