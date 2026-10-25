from whycode.retrieval.distiller import DistilledSource
from whycode.retrieval.verifier import CitationVerifier


def _make_source(source_id: int, file_path: str, start_line: int, end_line: int) -> DistilledSource:
    return DistilledSource(
        source_id=source_id,
        file_path=file_path,
        start_line=start_line,
        end_line=end_line,
        content="some code content",
    )


def test_verifier_validates_source_id_citation() -> None:
    sources = [
        _make_source(1, "src/whycode/llm/cache.py", 10, 30),
        _make_source(2, "src/whycode/llm/gemini.py", 20, 50),
    ]

    answer = "The cache key is built in [Source 1], while rate limits are handled in [Source 2]."
    verifier = CitationVerifier()
    res = verifier.verify(answer, sources)

    assert len(res.citations) == 2
    assert res.all_verified is True
    assert res.grounding_confidence == 1.0
    assert res.citations[0].is_verified is True
    assert res.citations[1].is_verified is True


def test_verifier_validates_file_and_line_range_citation() -> None:
    sources = [
        _make_source(1, "src/whycode/llm/cache.py", 10, 40),
    ]

    # Cited line range 15-25 is within 10-40
    answer = "The DiskCache class is located at cache.py:15-25."
    verifier = CitationVerifier()
    res = verifier.verify(answer, sources)

    assert len(res.citations) == 1
    assert res.citations[0].is_verified is True
    assert res.grounding_confidence == 1.0


def test_verifier_detects_hallucinated_file() -> None:
    sources = [
        _make_source(1, "src/whycode/llm/cache.py", 10, 40),
    ]

    # Model hallucinates a file nonexistent.py
    answer = "Authentication is configured in nonexistent.py:5-10."
    verifier = CitationVerifier()
    res = verifier.verify(answer, sources)

    assert len(res.citations) == 1
    assert res.citations[0].is_verified is False
    assert "was not in the retrieved sources" in res.citations[0].reason
    assert res.grounding_confidence == 0.0
    assert res.all_verified is False


def test_verifier_detects_out_of_range_lines() -> None:
    sources = [
        _make_source(1, "cache.py", 10, 20),
    ]

    # Lines 80-95 are completely outside 10-20
    answer = "Refer to cache.py:80-95 for details."
    verifier = CitationVerifier()
    res = verifier.verify(answer, sources)

    assert len(res.citations) == 1
    assert res.citations[0].is_verified is False
    assert "outside retrieved line span" in res.citations[0].reason
    assert res.grounding_confidence == 0.0


def test_verifier_calculates_mixed_confidence() -> None:
    sources = [
        _make_source(1, "cache.py", 1, 30),
    ]

    answer = "Valid part is in cache.py:10-20, but fake part is in fake.py:1-5."
    verifier = CitationVerifier()
    res = verifier.verify(answer, sources)

    assert len(res.citations) == 2
    assert res.citations[0].is_verified is True
    assert res.citations[1].is_verified is False
    assert res.grounding_confidence == 0.5
    assert res.all_verified is False


def test_verifier_handles_empty_text_and_no_citations() -> None:
    sources = [_make_source(1, "demo.py", 1, 10)]
    verifier = CitationVerifier()

    res_empty = verifier.verify("", sources)
    assert res_empty.grounding_confidence == 0.0

    res_no_cits = verifier.verify("This is a generic statement without citations.", sources)
    assert res_no_cits.grounding_confidence == 1.0
    assert res_no_cits.citations == ()
