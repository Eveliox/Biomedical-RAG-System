"""Cross-encoder reranker via sentence-transformers.

Uses `cross-encoder/ms-marco-MiniLM-L-6-v2` by default — a widely-used, small
model that runs comfortably on CPU. First call downloads ~90 MB of weights;
cached thereafter.
"""
from __future__ import annotations

import logging
from functools import lru_cache

from app.config import get_settings

logger = logging.getLogger(__name__)


class CrossEncoderReranker:
    def __init__(self, model_name: str) -> None:
        from sentence_transformers import CrossEncoder

        logger.info("loading reranker %s", model_name)
        self._model = CrossEncoder(model_name)
        logger.info("reranker ready")

    def score(self, query: str, passages: list[str]) -> list[float]:
        if not passages:
            return []
        pairs = [(query, p) for p in passages]
        scores = self._model.predict(pairs, show_progress_bar=False)
        return [float(s) for s in scores]


@lru_cache
def get_reranker() -> CrossEncoderReranker | None:
    settings = get_settings()
    if not settings.reranker_enabled:
        return None
    return CrossEncoderReranker(settings.reranker_model)
