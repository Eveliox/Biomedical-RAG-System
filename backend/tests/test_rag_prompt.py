"""Prompt construction should be deterministic and follow the citation contract."""
from app.prompts.rag_prompt import ContextChunk, build_rag_prompt, format_context_block


def test_context_block_includes_citation_number_and_pmid():
    block = format_context_block(
        ContextChunk(citation_number=1, pmid="12345", title="Title", text="Body")
    )
    assert "SOURCE [1]" in block
    assert "PMID: 12345" in block
    assert "Body" in block


def test_prompt_contains_rules_and_all_sources():
    chunks = [
        ContextChunk(1, "111", "First paper", "text one"),
        ContextChunk(2, "222", "Second paper", "text two"),
    ]
    prompt = build_rag_prompt("what genes?", chunks)
    assert "biomedical literature research assistant" in prompt
    assert "SOURCE [1]" in prompt
    assert "SOURCE [2]" in prompt
    assert "what genes?" in prompt


def test_empty_context_still_renders_a_prompt():
    prompt = build_rag_prompt("orphan question", [])
    assert "(no sources)" in prompt
    assert "orphan question" in prompt


def test_source_numbering_is_1_based_and_matches_position():
    chunks = [ContextChunk(i, f"pmid{i}", f"t{i}", f"body{i}") for i in range(1, 4)]
    prompt = build_rag_prompt("q", chunks)
    # The Nth SOURCE block should mention "pmidN".
    for i in range(1, 4):
        assert f"SOURCE [{i}]" in prompt
        assert f"pmid{i}" in prompt
