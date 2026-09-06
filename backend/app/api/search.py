"""GET /api/search — keyword search over PubMed.

Route is deliberately thin: parse query args, call service, return.
Any real logic (retrying, parsing) belongs in the service layer.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.models.schemas import SearchResponse
from app.services.pubmed_service import (
    PubMedClient,
    PubMedError,
    get_pubmed_client,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["search"])


@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=2, description="PubMed search query"),
    limit: int = Query(10, ge=1, le=50, description="Max papers to return"),
    client: PubMedClient = Depends(get_pubmed_client),
) -> SearchResponse:
    try:
        pmids = await client.search(q, limit=limit)
        papers = await client.fetch(pmids)
    except PubMedError as exc:
        logger.exception("pubmed error for q=%r", q)
        raise HTTPException(status_code=502, detail=f"PubMed error: {exc}") from exc
    except Exception as exc:  # network / timeout / parsing
        logger.exception("unexpected error during search")
        raise HTTPException(status_code=502, detail="Upstream PubMed failure") from exc

    return SearchResponse(query=q, papers=papers)
