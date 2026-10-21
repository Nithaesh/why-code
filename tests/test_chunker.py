
from pathlib import Path

import pytest

from whycode.ingest.chunker import (
    CodeChunk,
    CodeChunker,
    ChunkerConfig,
    make_chunk_id,
)


def test_empty_content_returns_no_chunks() -> None:
    assert CodeChunker().chunk_text("src/main.py", "") == []


def test_short_file_creates_one_chunk() -> None:
    chunker = CodeChunker(ChunkerConfig(max_lines=5, overlap_lines=1))

    chunks = chunker.chunk_text(
        "src/main.py",
        "line one\nline two\nline three",
    )

    assert len(chunks) == 1
    assert chunks[0].file_path == "src/main.py"
    assert chunks[0].start_line == 1
    assert chunks[0].end_line == 3
    assert chunks[0].content == "line one\nline two\nline three"


def test_long_file_creates_overlapping_chunks() -> None:
    content = "\n".join(f"line {i}" for i in range(1, 9))
    chunker = CodeChunker(ChunkerConfig(max_lines=5, overlap_lines=2))

    chunks = chunker.chunk_text("src/main.py", content)

    assert [(c.start_line, c.end_line) for c in chunks] == [
        (1, 5),
        (4, 8),
    ]
    assert chunks[1].content.startswith("line 4\nline 5")


def test_zero_overlap_splits_without_shared_lines() -> None:
    content = "\n".join(f"line {i}" for i in range(1, 8))
    chunker = CodeChunker(ChunkerConfig(max_lines=3, overlap_lines=0))

    chunks = chunker.chunk_text("src/main.py", content)

    assert [(c.start_line, c.end_line) for c in chunks] == [
        (1, 3),
        (4, 6),
        (7, 7),
    ]


def test_chunk_ids_are_deterministic() -> None:
    first = make_chunk_id("src/main.py", 1, 2, "a\nb")
    second = make_chunk_id("src/main.py", 1, 2, "a\nb")

    assert first == second


def test_chunk_ids_change_when_content_changes() -> None:
    first = make_chunk_id("src/main.py", 1, 2, "a\nb")
    second = make_chunk_id("src/main.py", 1, 2, "a\nc")

    assert first != second


def test_windows_paths_are_normalized() -> None:
    chunks = CodeChunker().chunk_text(
        r"src\auth\login.py",
        "def login():\n    pass",
    )

    assert chunks[0].file_path == "src/auth/login.py"


@pytest.mark.parametrize(
    "path",
    [
        "",
        "../outside.py",
        "src/../../outside.py",
        "/absolute/path.py",
    ],
)
def test_rejects_invalid_paths(path: str) -> None:
    with pytest.raises(ValueError):
        CodeChunker().chunk_text(path, "print('hello')")


def test_rejects_invalid_chunker_configuration() -> None:
    with pytest.raises(ValueError):
        ChunkerConfig(max_lines=0)

    with pytest.raises(ValueError):
        ChunkerConfig(max_lines=5, overlap_lines=5)


def test_code_chunk_rejects_invalid_line_ranges() -> None:
    with pytest.raises(ValueError):
        CodeChunk(
            chunk_id="id",
            file_path="src/main.py",
            start_line=0,
            end_line=2,
            content="hello",
        )

def test_rejects_windows_absolute_path() -> None:
    with pytest.raises(ValueError):
        CodeChunker().chunk_text(
            r"C:\Users\someone\main.py",
            "print('hello')",
        )


def test_newline_only_content_returns_no_chunks() -> None:
    assert CodeChunker().chunk_text(
        "src/main.py",
        "\n",
    ) == []
def test_rejects_windows_absolute_path() -> None:
    with pytest.raises(ValueError):
        CodeChunker().chunk_text(
            r"C:\Users\someone\main.py",
            "print('hello')",
        )


def test_newline_only_content_returns_no_chunks() -> None:
    assert CodeChunker().chunk_text(
        "src/main.py",
        "\n",
    ) == []