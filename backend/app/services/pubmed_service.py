"""Client for NCBI's Entrez (E-utilities) API — the programmatic way to query PubMed.

Two endpoints are all we need for the MVP:

    esearch.fcgi   →  keyword query        →  list of PMIDs
    efetch.fcgi    →  PMIDs                 →  XML with titles/abstracts/authors

NCBI etiquette: send `tool=` and `email=` on every request, and don't exceed
3 req/s without an API key (10 req/s with one). We use httpx.AsyncClient so
FastAPI's event loop isn't blocked while we wait.
"""
from __future__ import annotations

import logging
from typing import Any
from xml.etree import ElementTree as ET

import httpx

from app.config import get_settings
from app.models.paper import Paper

logger = logging.getLogger(__name__)

ENTREZ_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
TOOL_NAME = "biomedical-rag-system"


class PubMedError(RuntimeError):
    """Raised when PubMed returns something we can't work with."""


class PubMedClient:
    """Thin async wrapper around Entrez esearch + efetch.

    Instances are cheap; a single client can be reused across requests.
    """

    def __init__(self, timeout: float = 15.0) -> None:
        settings = get_settings()
        self._email = settings.ncbi_email
        self._api_key = settings.ncbi_api_key
        self._timeout = timeout

    def _common_params(self) -> dict[str, str]:
        params = {"tool": TOOL_NAME, "email": self._email}
        if self._api_key:
            params["api_key"] = self._api_key
        return params

    async def search(self, query: str, limit: int = 10) -> list[str]:
        """Return a list of PMIDs matching the query, most-relevant first."""
        params = {
            **self._common_params(),
            "db": "pubmed",
            "term": query,
            "retmax": str(limit),
            "retmode": "json",
            "sort": "relevance",
        }
        url = f"{ENTREZ_BASE}/esearch.fcgi"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        try:
            pmids = data["esearchresult"]["idlist"]
        except KeyError as exc:
            raise PubMedError(f"Unexpected esearch payload: {data!r}") from exc
        logger.info("pubmed.search q=%r limit=%d hits=%d", query, limit, len(pmids))
        return list(pmids)

    async def fetch(self, pmids: list[str]) -> list[Paper]:
        """Fetch article metadata + abstracts for the given PMIDs."""
        if not pmids:
            return []
        params = {
            **self._common_params(),
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
        }
        url = f"{ENTREZ_BASE}/efetch.fcgi"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            xml_text = resp.text

        papers = _parse_pubmed_xml(xml_text)
        logger.info("pubmed.fetch requested=%d parsed=%d", len(pmids), len(papers))
        return papers


# ---------------------------------------------------------------------------
# XML parsing (pure function so we can unit-test it without hitting the network)
# ---------------------------------------------------------------------------

def _text(node: ET.Element | None) -> str:
    """Return the text of an element (including children), stripped. '' if None."""
    if node is None:
        return ""
    # itertext() concatenates all descendant text — handles <i>, <b>, <sub> inside abstracts.
    return "".join(node.itertext()).strip()


def _parse_pubmed_xml(xml_text: str) -> list[Paper]:
    root = ET.fromstring(xml_text)
    papers: list[Paper] = []
    for article in root.findall(".//PubmedArticle"):
        pmid = _text(article.find(".//MedlineCitation/PMID"))
        if not pmid:
            continue

        title = _text(article.find(".//Article/ArticleTitle"))

        # Abstracts may be split across multiple <AbstractText> nodes with Labels
        # (BACKGROUND, METHODS, RESULTS, CONCLUSIONS). Concatenate them.
        abstract_parts: list[str] = []
        for at in article.findall(".//Abstract/AbstractText"):
            label = at.attrib.get("Label")
            text = _text(at)
            if not text:
                continue
            abstract_parts.append(f"{label}: {text}" if label else text)
        abstract = "\n".join(abstract_parts)

        authors: list[str] = []
        for author in article.findall(".//AuthorList/Author"):
            last = _text(author.find("LastName"))
            initials = _text(author.find("Initials"))
            collective = _text(author.find("CollectiveName"))
            if last:
                authors.append(f"{last} {initials}".strip())
            elif collective:
                authors.append(collective)

        journal = _text(article.find(".//Journal/Title"))

        # Publication date: prefer PubDate/Year; fall back to MedlineDate string.
        pub_year = _text(article.find(".//Journal/JournalIssue/PubDate/Year"))
        pub_month = _text(article.find(".//Journal/JournalIssue/PubDate/Month"))
        if pub_year and pub_month:
            publication_date = f"{pub_year}-{pub_month}"
        elif pub_year:
            publication_date = pub_year
        else:
            publication_date = _text(
                article.find(".//Journal/JournalIssue/PubDate/MedlineDate")
            )

        doi: str | None = None
        for aid in article.findall(".//ArticleIdList/ArticleId"):
            if aid.attrib.get("IdType") == "doi":
                doi = _text(aid) or None
                break

        papers.append(
            Paper(
                pmid=pmid,
                title=title,
                abstract=abstract,
                authors=authors,
                journal=journal,
                publication_date=publication_date,
                doi=doi,
            )
        )
    return papers


# Export a parsing function for tests that don't want to instantiate a client.
def parse_pubmed_xml(xml_text: str) -> list[Paper]:
    """Public alias for the internal XML parser."""
    return _parse_pubmed_xml(xml_text)


# Convenience factory used by FastAPI dependency injection later.
def get_pubmed_client() -> PubMedClient:
    return PubMedClient()


__all__ = ["PubMedClient", "PubMedError", "get_pubmed_client", "parse_pubmed_xml"]


# For simple manual testing:  `python -m app.services.pubmed_service "brca2"`
if __name__ == "__main__":  # pragma: no cover
    import asyncio
    import sys

    async def _demo() -> None:
        client = PubMedClient()
        query = sys.argv[1] if len(sys.argv) > 1 else "pancreatic cancer"
        ids = await client.search(query, limit=3)
        papers = await client.fetch(ids)
        for p in papers:
            print(f"[{p.pmid}] {p.title}\n  {p.journal} · {p.publication_date}\n")

    asyncio.run(_demo())
