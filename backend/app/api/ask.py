"""POST /api/ask — grounded question answering with citations."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.models.schemas import AskRequest, AskResponse
from app.services.rag_service import RAGService, get_rag_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["ask"])


@router.post("/ask", response_model=AskResponse)
async def ask(
    body: AskRequest,
    service: RAGService = Depends(get_rag_service),
) -> AskResponse:
    try:
        result = await service.ask(body.question, top_k=body.top_k)
    except Exception as exc:
        logger.exception("rag pipeline failed")
        raise HTTPException(status_code=500, detail="Failed to answer question") from exc

    return AskResponse(
        question=body.question,
        answer=result.answer,
        sources=result.sources,
    )
