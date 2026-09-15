"""Read-only aggregate views over the vector store.

Powers the /api/library/stats endpoint and (later) the /insights dashboard.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from app.vectorstore.chroma_store import get_vector_store


def _year(publication_date: str) -> int | None:
    """Pull a 4-digit year out of a publication_date string.

    NCBI mixes formats ("2024", "2024-Mar", "2024 Mar-Apr", "Winter 2023"),
    so we just grep the first 4-digit run that looks like a plausible year.
    """
    for i in range(len(publication_date) - 3):
        chunk = publication_date[i : i + 4]
        if chunk.isdigit():
            y = int(chunk)
            if 1900 <= y <= 2100:
                return y
    return None


@dataclass
class LibraryStats:
    paper_count: int
    chunk_count: int
    journal_count: int
    top_journals: list[tuple[str, int]] = field(default_factory=list)
    year_range: tuple[int | None, int | None] = (None, None)


class LibraryService:
    def __init__(self, vector_store=None) -> None:
        self._store = vector_store or get_vector_store()

    def stats(self, top_n_journals: int = 5) -> LibraryStats:
        metas = self._store.all_metadatas()
        chunk_count = len(metas)

        # One paper can produce many chunks — dedup by pmid before counting.
        by_pmid: dict[str, dict] = {}
        for m in metas:
            pmid = m.get("pmid")
            if pmid and pmid not in by_pmid:
                by_pmid[pmid] = m

        journal_counter: Counter[str] = Counter()
        years: list[int] = []
        for m in by_pmid.values():
            j = (m.get("journal") or "").strip()
            if j:
                journal_counter[j] += 1
            y = _year(m.get("publication_date") or "")
            if y:
                years.append(y)

        return LibraryStats(
            paper_count=len(by_pmid),
            chunk_count=chunk_count,
            journal_count=len(journal_counter),
            top_journals=journal_counter.most_common(top_n_journals),
            year_range=(min(years), max(years)) if years else (None, None),
        )


def get_library_service() -> LibraryService:
    return LibraryService()
