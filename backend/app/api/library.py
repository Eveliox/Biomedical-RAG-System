"""GET /api/library/stats + /insights — aggregate views over the corpus."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.models.schemas import (
    JournalCount,
    LibraryInsightsResponse,
    LibraryStatsResponse,
    NameCount,
    YearCount,
)
from app.services.library_service import (
    LibraryService,
    _InsightsAdapter,
    get_insights_service,
    get_library_service,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/library", tags=["library"])


@router.get("/stats", response_model=LibraryStatsResponse)
def stats(
    service: LibraryService = Depends(get_library_service),
) -> LibraryStatsResponse:
    try:
        s = service.stats()
    except Exception as exc:
        logger.exception("library stats failed")
        raise HTTPException(status_code=500, detail="Stats failed") from exc

    return LibraryStatsResponse(
        paper_count=s.paper_count,
        chunk_count=s.chunk_count,
        journal_count=s.journal_count,
        top_journals=[JournalCount(journal=j, count=c) for j, c in s.top_journals],
        year_min=s.year_range[0],
        year_max=s.year_range[1],
    )


@router.get("/insights", response_model=LibraryInsightsResponse)
def insights(
    service: _InsightsAdapter = Depends(get_insights_service),
) -> LibraryInsightsResponse:
    try:
        i = service.insights()
    except Exception as exc:
        logger.exception("library insights failed")
        raise HTTPException(status_code=500, detail="Insights failed") from exc

    return LibraryInsightsResponse(
        papers_per_year=[YearCount(year=y, count=c) for y, c in i.papers_per_year],
        top_genes=[NameCount(name=n, count=c) for n, c in i.top_genes],
        top_journals=[NameCount(name=n, count=c) for n, c in i.top_journals],
        top_authors=[NameCount(name=n, count=c) for n, c in i.top_authors],
    )
