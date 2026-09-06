"""Break long text into overlapping chunks for embedding.

Why chunk at all?
  Embedding models have a max input size (e.g. 512 tokens for MiniLM).
  If we embed a whole abstract as one vector, we lose fine-grained meaning —
  the vector becomes an "average" of everything the abstract says.
  Chunks give us multiple vectors per paper, each capturing a local idea.

Why overlap?
  A sentence that spans a chunk boundary would otherwise be split. Overlap
  ensures each idea appears in at least one chunk with enough surrounding context.

We use a *character-based* approximation of tokens (roughly 4 chars ≈ 1 token
for English biomedical text). This is good enough for chunk sizing without
pulling in a tokenizer as a dependency here.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# Roughly: split by paragraph, then by sentence. Biomedical abstracts often
# have long sentences, so we're conservative about splitting inside a sentence.
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(])")


@dataclass(frozen=True)
class Chunk:
    text: str
    index: int  # position within the source document


def _approx_char_budget(tokens: int) -> int:
    """Convert a token budget to a character budget (~4 chars/token)."""
    return max(1, tokens * 4)


def _split_into_sentences(text: str) -> list[str]:
    """Naive sentence splitter tuned for scientific prose.

    A proper solution would use spaCy or scispaCy — but that's a heavy dep
    for a modest quality gain in the MVP. Revisit in Phase 2.
    """
    # First split on blank lines (paragraphs / labeled abstract sections),
    # then split each paragraph on sentence boundaries.
    sentences: list[str] = []
    for para in re.split(r"\n\s*\n", text.strip()):
        para = para.strip()
        if not para:
            continue
        sentences.extend(s.strip() for s in _SENT_SPLIT.split(para) if s.strip())
    return sentences


def chunk_text(
    text: str,
    chunk_size_tokens: int = 600,
    chunk_overlap_tokens: int = 120,
) -> list[Chunk]:
    """Return a list of chunks approximately `chunk_size_tokens` long.

    Guarantees:
      - Each chunk contains whole sentences (never a mid-sentence cut).
      - Consecutive chunks share ~`chunk_overlap_tokens` worth of trailing text.
      - Empty input yields an empty list.
    """
    text = (text or "").strip()
    if not text:
        return []

    char_budget = _approx_char_budget(chunk_size_tokens)
    overlap_chars = _approx_char_budget(chunk_overlap_tokens)

    sentences = _split_into_sentences(text)
    if not sentences:
        return [Chunk(text=text, index=0)]

    chunks: list[Chunk] = []
    current: list[str] = []
    current_len = 0

    def flush() -> None:
        nonlocal current, current_len
        if not current:
            return
        chunk_text_ = " ".join(current).strip()
        chunks.append(Chunk(text=chunk_text_, index=len(chunks)))

    for sent in sentences:
        sent_len = len(sent) + 1  # +1 for the joining space
        if current_len + sent_len > char_budget and current:
            flush()
            # Start next chunk with the tail of the previous one for overlap.
            if overlap_chars > 0:
                tail = " ".join(current)[-overlap_chars:].split(" ", 1)
                # Drop the first (possibly partial) word to keep whole tokens.
                overlap_text = tail[1] if len(tail) > 1 else ""
                current = [overlap_text] if overlap_text else []
                current_len = len(overlap_text)
            else:
                current = []
                current_len = 0
        current.append(sent)
        current_len += sent_len

    flush()
    return chunks
