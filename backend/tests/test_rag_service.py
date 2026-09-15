"""Exercises the RAG service with fakes — no network, no model downloads.

Covers the two things easy to break in RAG:
  1. Dedup by pmid (multiple chunks from same paper -> one citation slot).
  2. Citation numbering matches sources[] position.
"""
import pytest

from app.services.rag_service import RAGService
from app.vectorstore.base import SearchHit


class FakeEmbedder:
    dimension = 4
    def embed_query(self, text): return [0.1, 0.2, 0.3, 0.4]
    def embed_documents(self, texts): return [[0.0] * 4 for _ in texts]


class FakeStore:
    def __init__(self, hits): self._hits = hits
    def similarity_search(self, q, k=5): return self._hits[:k]
    def add(self, records): pass
    def existing_pmids(self, pmids): return set()
    def count(self): return len(self._hits)


class FakeLLM:
    def __init__(self): self.last_prompt = None
    async def generate(self, prompt, *, temperature=0.1):
        self.last_prompt = prompt
        return "KRAS mutations are common [1]. TP53 alterations occur too [2]."


def _hit(pmid: str, score: float, text: str = "some chunk text") -> SearchHit:
    return SearchHit(
        id=f"{pmid}:0",
        text=text,
        metadata={
            "pmid": pmid,
            "title": f"Paper {pmid}",
            "journal": "Journal X",
            "publication_date": "2024",
            "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        },
        score=score,
    )


@pytest.mark.asyncio
async def test_dedup_collapses_multiple_chunks_from_same_paper():
    hits = [
        _hit("111", 0.90, "chunk A of paper 111"),
        _hit("111", 0.80, "chunk B of paper 111"),
        _hit("222", 0.75, "chunk of paper 222"),
    ]
    svc = RAGService(vector_store=FakeStore(hits), embedder=FakeEmbedder(), llm=FakeLLM())
    result = await svc.ask("question?", top_k=3)
    pmids = [s.pmid for s in result.sources]
    assert pmids == ["111", "222"]  # 111 appears once even though 2 chunks matched


@pytest.mark.asyncio
async def test_dedup_keeps_highest_scoring_chunk_text():
    hits = [
        _hit("111", 0.60, "low-score chunk"),
        _hit("111", 0.95, "high-score chunk"),
    ]
    fake_llm = FakeLLM()
    svc = RAGService(vector_store=FakeStore(hits), embedder=FakeEmbedder(), llm=fake_llm)
    await svc.ask("q", top_k=2)
    # The higher-scoring chunk's text is what got put into the prompt.
    assert "high-score chunk" in fake_llm.last_prompt
    assert "low-score chunk" not in fake_llm.last_prompt


@pytest.mark.asyncio
async def test_citation_number_matches_sources_position():
    hits = [
        _hit("aaa", 0.9),
        _hit("bbb", 0.8),
        _hit("ccc", 0.7),
    ]
    fake_llm = FakeLLM()
    svc = RAGService(vector_store=FakeStore(hits), embedder=FakeEmbedder(), llm=fake_llm)
    result = await svc.ask("q", top_k=3)
    # sources[0] is the paper we labeled SOURCE [1] in the prompt.
    assert result.sources[0].pmid == "aaa"
    assert result.sources[1].pmid == "bbb"
    assert result.sources[2].pmid == "ccc"
    assert "SOURCE [1]\nPMID: aaa" in fake_llm.last_prompt
    assert "SOURCE [3]\nPMID: ccc" in fake_llm.last_prompt


@pytest.mark.asyncio
async def test_empty_store_returns_helpful_answer_without_calling_llm():
    fake_llm = FakeLLM()
    svc = RAGService(vector_store=FakeStore([]), embedder=FakeEmbedder(), llm=fake_llm)
    result = await svc.ask("q", top_k=3)
    assert result.sources == []
    assert fake_llm.last_prompt is None  # LLM was NOT called
    assert "ingesting" in result.answer.lower()
