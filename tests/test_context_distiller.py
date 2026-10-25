import pytest

from whycode.ingest.chunker import CodeChunk
from whycode.retrieval.distiller import ContextDistiller
from whycode.retrieval.lexical import RetrievalResult


def _make_result(file_path: str, start_line: int, end_line: int, content: str, score: float = 1.0) -> RetrievalResult:
    chunk = CodeChunk(
        chunk_id=f"{file_path}:{start_line}-{end_line}",
        file_path=file_path,
        start_line=start_line,
        end_line=end_line,
        content=content,
    )
    return RetrievalResult(chunk=chunk, score=score)


def test_distiller_merges_overlapping_chunks_from_same_file() -> None:
    # Chunk 1: lines 1-3, Chunk 2: lines 2-4 (overlapping)
    r1 = _make_result("cache.py", 1, 3, "line 1\nline 2\nline 3")
    r2 = _make_result("cache.py", 2, 4, "line 2\nline 3\nline 4")

    distiller = ContextDistiller()
    distilled = distiller.distill([r1, r2])

    assert len(distilled.sources) == 1
    src = distilled.sources[0]
    assert src.file_path == "cache.py"
    assert src.start_line == 1
    assert src.end_line == 4
    assert src.content == "line 1\nline 2\nline 3\nline 4"
    assert not distilled.truncated


def test_distiller_merges_adjacent_chunks() -> None:
    # Chunk 1: lines 1-2, Chunk 2: lines 3-4 (adjacent)
    r1 = _make_result("math.py", 1, 2, "a = 1\nb = 2")
    r2 = _make_result("math.py", 3, 4, "c = 3\nd = 4")

    distiller = ContextDistiller()
    distilled = distiller.distill([r1, r2])

    assert len(distilled.sources) == 1
    assert distilled.sources[0].start_line == 1
    assert distilled.sources[0].end_line == 4
    assert distilled.sources[0].content == "a = 1\nb = 2\nc = 3\nd = 4"


def test_distiller_keeps_disjoint_chunks_separate() -> None:
    # Chunk 1: lines 1-2, Chunk 2: lines 10-12 (disjoint)
    r1 = _make_result("server.py", 1, 2, "import os\nimport sys")
    r2 = _make_result("server.py", 10, 12, "def start():\n    pass")

    distiller = ContextDistiller()
    distilled = distiller.distill([r1, r2])

    assert len(distilled.sources) == 2
    assert distilled.sources[0].start_line == 1
    assert distilled.sources[0].end_line == 2
    assert distilled.sources[1].start_line == 10
    assert distilled.sources[1].end_line == 12


def test_distiller_preserves_multiple_files_order() -> None:
    r1 = _make_result("auth.py", 1, 3, "def login(): pass")
    r2 = _make_result("db.py", 5, 8, "def query(): pass")
    r3 = _make_result("auth.py", 2, 4, "def logout(): pass")

    distiller = ContextDistiller()
    distilled = distiller.distill([r1, r2, r3])

    # auth.py should appear first (merged), then db.py
    assert len(distilled.sources) == 2
    assert distilled.sources[0].file_path == "auth.py"
    assert distilled.sources[1].file_path == "db.py"


def test_distiller_enforces_character_budget() -> None:
    r1 = _make_result("first.py", 1, 5, "x" * 200)
    r2 = _make_result("second.py", 1, 5, "y" * 200)

    # Budget only enough for one block
    distiller = ContextDistiller(max_context_chars=350)
    distilled = distiller.distill([r1, r2])

    assert len(distilled.sources) == 1
    assert distilled.sources[0].file_path == "first.py"
    assert distilled.truncated is True


def test_distiller_handles_empty_results() -> None:
    distiller = ContextDistiller()
    distilled = distiller.distill([])

    assert distilled.text == ""
    assert distilled.sources == ()
    assert distilled.total_chars == 0
    assert not distilled.truncated


def test_distiller_rejects_nonpositive_budget() -> None:
    with pytest.raises(ValueError, match="max_context_chars must be positive"):
        ContextDistiller(max_context_chars=0)
