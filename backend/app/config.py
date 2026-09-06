"""Application configuration loaded from environment variables.

Using pydantic-settings means:
  - each field is typed and validated on startup,
  - missing/malformed env vars fail loudly instead of surprising us at runtime,
  - defaults live in one place.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- NCBI / PubMed ---
    # NCBI requires (or strongly recommends) an email so they can contact you
    # if your script misbehaves. An API key raises the rate limit from 3 to 10 req/s.
    ncbi_email: str = Field(default="anonymous@example.com")
    ncbi_api_key: str | None = Field(default=None)

    # --- Embeddings (local sentence-transformers) ---
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")

    # --- LLM (local Ollama) ---
    ollama_base_url: str = Field(default="http://localhost:11434")
    llm_model: str = Field(default="llama3.2:3b")

    # --- RAG ---
    chunk_size: int = Field(default=600)
    chunk_overlap: int = Field(default=120)
    rag_top_k: int = Field(default=6)

    # --- Vector store ---
    chroma_persist_dir: str = Field(default="./data/chroma_db")
    chroma_collection: str = Field(default="pubmed_chunks")


@lru_cache
def get_settings() -> Settings:
    """Cached accessor so we don't re-parse env on every request."""
    return Settings()
