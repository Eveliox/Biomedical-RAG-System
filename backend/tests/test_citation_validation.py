"""Tests for the hallucination check on model output."""
from app.services.rag_service import find_invalid_citations


def test_all_valid_returns_empty_list():
    answer = "KRAS is common [1]. TP53 is too [2][3]."
    assert find_invalid_citations(answer, source_count=3) == []


def test_out_of_range_citation_is_flagged():
    answer = "This claim [1] is real, but [7] is not."
    assert find_invalid_citations(answer, source_count=3) == [7]


def test_multiple_invalid_citations_all_reported():
    answer = "Nonsense [9] and also [10] and yet again [11]."
    assert find_invalid_citations(answer, source_count=2) == [9, 10, 11]


def test_no_citations_at_all():
    assert find_invalid_citations("Plain sentence with no brackets.", 3) == []


def test_zero_index_is_invalid():
    # Sources are 1-based; [0] should never appear.
    assert find_invalid_citations("bogus [0]", source_count=3) == [0]


def test_duplicates_are_reported_each_time():
    # If a model spams [7] three times we want to know that too.
    answer = "[7] said A. [7] said B. Real one [1]."
    assert find_invalid_citations(answer, source_count=3) == [7, 7]
