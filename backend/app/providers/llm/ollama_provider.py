"""Ollama-backed LLM provider.

Ollama runs models locally and exposes an HTTP API on :11434.
Run `ollama serve` and `ollama pull llama3.2:3b` before using this.

Supports both one-shot (`generate`) and streaming (`stream`) calls against
`/api/generate`. Streaming yields Ollama's NDJSON events one line at a time.
"""
from __future__ import annotations

import json
import logging
from typing import AsyncIterator

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

    async def stream(
        self, prompt: str, *, temperature: float = 0.1
    ) -> AsyncIterator[str]:
        """Yield response chunks as they arrive from Ollama."""
        url = f"{self._base_url}/api/generate"
        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": True,
            "options": {"temperature": temperature},
        }
        chunk_count = 0
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            async with client.stream("POST", url, json=payload) as resp:
                resp.raise_for_status()
                async for raw_line in resp.aiter_lines():
                    if not raw_line:
                        continue
                    try:
                        data = json.loads(raw_line)
                    except json.JSONDecodeError:
                        continue
                    if piece := data.get("response"):
                        chunk_count += 1
                        yield piece
                    if data.get("done"):
                        break
        logger.info(
            "ollama.stream model=%s prompt_chars=%d chunks=%d",
            self._model,
            len(prompt),
            chunk_count,
        )


def get_llm_provider() -> OllamaProvider:
    settings = get_settings()
    return OllamaProvider(base_url=settings.ollama_base_url, model=settings.llm_model)
