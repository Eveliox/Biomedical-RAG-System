"""Turn a list of PMIDs into stored, searchable chunks.

Pipeline for each PMID:
    fetch metadata + abstract  →  chunk text  →  embed chunks  →  save to vector store

Skips PMIDs that are already indexed (by looking them up in the store first),
so re-ingesting the same paper is a no-op.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from app.config import get_settings
from app.models.paper import Paper
from app.providers.embeddings.sentence_transformers_provider import (
    get_embedding_provider,
)
from app.services.chunking_service import chunk_text
from app.services.pubmed_service import PubMedClient, get_pubmed_client
from app.vectorstore.base import VectorRecord
from app.vectorstore.chroma_store import get_vector_store

logger = logging.getLogger(__name__)


@dataclass
class IngestResult:
    ingested: list[str]
    skipped: list[str]
    failed: list[str]
    chunk_count: int


class IngestionService:
    def __init__(
        self,
        pubmed: PubMedClient | None = None,
        vector_store=None,
        embedder=None,
    ) -> None:
        self._pubmed = pubmed or get_pubmed_client()
        self._store = vector_store or get_vector_store()
        self._embedder = embedder or get_embedding_provider()
        self._settings = get_settings()

    async def ingest(self, pmids: list[str]) -> IngestResult:
        # 1. Dedup against what's already stored.
        already = self._store.existing_pmids(pmids)
        to_fetch = [p for p in pmids if p not in already]
        skipped = sorted(already)

        if not to_fetch:
            logger.info("ingest: nothing new (all %d already stored)", len(pmids))
            return IngestResult(ingested=[], skipped=skipped, failed=[], chunk_count=0)

        # 2. Fetch metadata + abstracts.
        try:
            papers = await self._pubmed.fetch(to_fetch)
        except Exception:
            logger.exception("pubmed fetch failed during ingestion")
            return IngestResult(
                ingested=[], skipped=skipped, failed=to_fetch, chunk_count=0
            )

        fetched_pmids = {p.pmid for p in papers}
        failed = [p for p in to_fetch if p not in fetched_pmids]

        # 3. Chunk + embed + store.
        records, ingested = self._build_records(papers)
        if records:
            self._store.add(records)

        logger.info(
            "ingest done: new=%d skipped=%d failed=%d chunks=%d",
            len(ingested),
            len(skipped),
            len(failed),
            len(records),
        )
        return IngestResult(
            ingested=ingested,
            skipped=skipped,
            failed=failed,
            chunk_count=len(records),
        )

    def _build_records(self, papers: list[Paper]) -> tuple[list[VectorRecord], list[str]]:
        records: list[VectorRecord] = []
        ingested: list[str] = []

        for paper in papers:
            text = paper.as_document_text()
            if not text.strip():
                logger.warning("skipping pmid=%s: no title/abstract", paper.pmid)
                continue

            chunks = chunk_text(
                text,
                chunk_size_tokens=self._settings.chunk_size,
                chunk_overlap_tokens=self._settings.chunk_overlap,
            )
            if not chunks:
                continue

            embeddings = self._embedder.embed_documents([c.text for c in chunks])
            for chunk, vec in zip(chunks, embeddings):
                records.append(
                    VectorRecord(
                        id=f"{paper.pmid}:{chunk.index}",
                        text=chunk.text,
                        embedding=vec,
                        metadata={
                            "pmid": paper.pmid,
                            "title": paper.title,
                            "authors": paper.authors,
                            "journal": paper.journal,
                            "publication_date": paper.publication_date,
                            "doi": paper.doi,
                            "chunk_index": chunk.index,
                            "pubmed_url": paper.pubmed_url,
                        },
                    )
                )
            ingested.append(paper.pmid)

        return records, ingested


def get_ingestion_service() -> IngestionService:
    return IngestionService()
