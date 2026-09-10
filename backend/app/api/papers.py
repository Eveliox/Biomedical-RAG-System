"""POST /api/papers/ingest — fetch, chunk, embed, and store papers by PMID."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.models.schemas import IngestRequest, IngestResponse
from app.services.ingestion_service import IngestionService, get_ingestion_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/papers", tags=["papers"])


@router.post("/ingest", response_model=IngestResponse)
async def ingest(
    body: IngestRequest,
    service: IngestionService = Depends(get_ingestion_service),
) -> IngestResponse:
    try:
        result = await service.ingest(body.pmids)
    except Exception as exc:
        logger.exception("ingestion pipeline failed")
        raise HTTPException(status_code=500, detail="Ingestion failed") from exc

    return IngestResponse(
        ingested=result.ingested,
        skipped=result.skipped,
        failed=result.failed,
        chunk_count=result.chunk_count,
    )
