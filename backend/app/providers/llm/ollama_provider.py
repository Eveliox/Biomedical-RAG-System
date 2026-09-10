"""Ollama-backed LLM provider.

Ollama runs models locally and exposes an HTTP API on :11434.
Run `ollama serve` and `ollama pull llama3.2:3b` before using this.

We use the `/api/generate` endpoint in non-streaming mode for simplicity.
"""
from __future__ import annotations

import logging

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


class OllamaProvider:
    def __init__(self, base_url: str, model: str, timeout: float = 120.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout

    async def generate(self, prompt: str, *, temperature: float = 0.1) -> str:
        url = f"{self._base_url}/api/generate"
        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "options": {
                # Low temperature keeps the answer close to the source text —
                # exactly what we want for a citation-grounded system.
                "temperature": temperature,
            },
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
        text = data.get("response", "")
        logger.info(
            "ollama.generate model=%s prompt_chars=%d out_chars=%d",
            self._model,
            len(prompt),
            len(text),
        )
        return text.strip()


def get_llm_provider() -> OllamaProvider:
    settings = get_settings()
    return OllamaProvider(base_url=settings.ollama_base_url, model=settings.llm_model)
