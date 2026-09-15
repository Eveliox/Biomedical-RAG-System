"""GET /api/library/stats — aggregate view of what's been ingested."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.models.schemas import JournalCount, LibraryStatsResponse
from app.services.library_service import LibraryService, get_library_service

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
