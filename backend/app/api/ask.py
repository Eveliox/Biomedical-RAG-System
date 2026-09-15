"""POST /api/ask — grounded question answering with citations.

Two variants:
  POST /api/ask        → wait, return the full answer + sources
  POST /api/ask/stream → newline-delimited JSON stream: sources first,
                          then token events, then a done event
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

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


@router.post("/ask/stream")
async def ask_stream(
    body: AskRequest,
    service: RAGService = Depends(get_rag_service),
) -> StreamingResponse:
    async def gen():
        try:
            async for event in service.ask_stream(body.question, top_k=body.top_k):
                yield event
        except Exception:
            logger.exception("streaming rag pipeline failed")
            yield '{"type":"error","message":"stream failed"}\n'

    return StreamingResponse(gen(), media_type="application/x-ndjson")
