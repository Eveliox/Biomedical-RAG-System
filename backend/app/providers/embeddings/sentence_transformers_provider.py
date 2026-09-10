"""Local embedding provider using sentence-transformers.

The first call downloads the model weights (~90 MB for MiniLM-L6-v2).
After that everything is offline and free.

Loading the model is slow (~1s), so we cache the instance via lru_cache.
"""
from __future__ import annotations

import logging
from functools import lru_cache

from app.config import get_settings

logger = logging.getLogger(__name__)


class SentenceTransformersProvider:
    def __init__(self, model_name: str) -> None:
        # Imported lazily so `import app.main` doesn't cost 2s at boot
        # in environments that never call embed_*.
        from sentence_transformers import SentenceTransformer

        logger.info("loading embedding model %s", model_name)
        self._model = SentenceTransformer(model_name)
        self.dimension: int = int(self._model.get_sentence_embedding_dimension())
        logger.info("embedding model ready dim=%d", self.dimension)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        # normalize_embeddings=True lets us use cosine similarity via dot product.
        vecs = self._model.encode(
            texts, batch_size=32, normalize_embeddings=True, show_progress_bar=False
        )
        return [v.tolist() for v in vecs]

    def embed_query(self, text: str) -> list[float]:
        vec = self._model.encode(
            [text], normalize_embeddings=True, show_progress_bar=False
        )[0]
        return vec.tolist()


@lru_cache
def get_embedding_provider() -> SentenceTransformersProvider:
    settings = get_settings()
    return SentenceTransformersProvider(settings.embedding_model)
