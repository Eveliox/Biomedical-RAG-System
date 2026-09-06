"""Normalized representation of a PubMed paper.

`Paper` is our internal shape. PubMed returns messy XML; we parse once
into this and use `Paper` everywhere else. That way the rest of the app
never sees XML.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class Paper(BaseModel):
    pmid: str
    title: str
    abstract: str = ""
    authors: list[str] = Field(default_factory=list)
    journal: str = ""
    publication_date: str = ""  # e.g. "2024" or "2024-03"
    doi: str | None = None

    @property
    def pubmed_url(self) -> str:
        return f"https://pubmed.ncbi.nlm.nih.gov/{self.pmid}/"

    def as_document_text(self) -> str:
        """Concatenate the fields worth embedding into one string.

        Title carries a lot of signal in biomedical papers, so we prepend it.
        Journal + date help disambiguate but aren't semantically useful for retrieval.
        """
        parts = [self.title.strip()]
        if self.abstract:
            parts.append(self.abstract.strip())
        return "\n\n".join(p for p in parts if p)
