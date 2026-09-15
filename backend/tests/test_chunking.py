"""Chunking is pure — no I/O — so these tests are fast and deterministic."""
from app.services.chunking_service import chunk_text


def test_empty_input_returns_no_chunks():
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_short_text_becomes_single_chunk():
    text = "Pancreatic cancer is aggressive. Early detection matters."
    chunks = chunk_text(text, chunk_size_tokens=200, chunk_overlap_tokens=20)
    assert len(chunks) == 1
    assert "aggressive" in chunks[0].text
    assert chunks[0].index == 0


def test_long_text_produces_multiple_chunks():
    # Build ~30 short sentences; with chunk_size_tokens=50 (~200 chars) we
    # should get several chunks.
    sentences = [f"Sentence number {i} about KRAS mutations." for i in range(30)]
    text = " ".join(sentences)
    chunks = chunk_text(text, chunk_size_tokens=50, chunk_overlap_tokens=10)
    assert len(chunks) > 1
    # Chunk indices are 0-based and monotonically increasing.
    assert [c.index for c in chunks] == list(range(len(chunks)))


def test_chunks_end_at_sentence_boundaries():
    text = " ".join([f"Sentence {i} ends here." for i in range(20)])
    chunks = chunk_text(text, chunk_size_tokens=40, chunk_overlap_tokens=8)
    # No chunk should end mid-word (i.e. the last non-space char is punctuation).
    for c in chunks:
        stripped = c.text.rstrip()
        assert stripped[-1] in ".!?", f"chunk didn't end at sentence: {stripped[-30:]!r}"


def test_overlap_preserves_context_across_chunks():
    text = " ".join([f"Sentence {i} discusses TP53." for i in range(20)])
    chunks = chunk_text(text, chunk_size_tokens=40, chunk_overlap_tokens=20)
    # If overlap works, some content from chunk N should reappear at the
    # start of chunk N+1.
    if len(chunks) >= 2:
        tail_words = set(chunks[0].text.split()[-3:])
        head_words = set(chunks[1].text.split()[:6])
        assert tail_words & head_words, "expected overlap between consecutive chunks"
