
from pathlib import Path

import pytest

from whycode.ingest.chunker import ChunkerConfig, CodeChunker
from whycode.ingest.pipeline import (
    IngestionError,
    RepositoryIngestionPipeline,
)
from whycode.ingest.scanner import RepositoryScanner


def test_ingests_source_files_into_chunks(tmp_path: Path):
    (tmp_path / "main.py").write_text(
        "def hello():\n    return 'hello'\n",
        encoding="utf-8",
    )
    (tmp_path / "notes.md").write_text(
        "# Project\nUseful notes\n",
        encoding="utf-8",
    )
    (tmp_path / ".env").write_text(
        "API_KEY=do-not-ingest",
        encoding="utf-8",
    )

    result = RepositoryIngestionPipeline(tmp_path).ingest()

    assert result.files_scanned == 2
    assert result.chunks_created == 2
    assert {chunk.file_path for chunk in result.chunks} == {
        "main.py",
        "notes.md",
    }
    assert all("do-not-ingest" not in chunk.content for chunk in result.chunks)


def test_preserves_chunk_line_numbers(tmp_path: Path):
    (tmp_path / "main.py").write_text(
        "\n".join(f"line_{number}" for number in range(1, 7)),
        encoding="utf-8",
    )

    pipeline = RepositoryIngestionPipeline(
        tmp_path,
        chunker=CodeChunker(
            ChunkerConfig(max_lines=3, overlap_lines=1)
        ),
    )

    result = pipeline.ingest()

    assert [(c.start_line, c.end_line) for c in result.chunks] == [
        (1, 3),
        (3, 5),
        (5, 6),
    ]


def test_empty_repository_produces_no_chunks(tmp_path: Path):
    result = RepositoryIngestionPipeline(tmp_path).ingest()

    assert result.files_scanned == 0
    assert result.chunks_created == 0
    assert result.chunks == ()


def test_rejects_nonexistent_repository(tmp_path: Path):
    missing = tmp_path / "does-not-exist"

    with pytest.raises(IngestionError, match="Could not scan repository"):
        RepositoryIngestionPipeline(missing).ingest()


def test_uses_injected_scanner_and_chunker(tmp_path: Path):
    (tmp_path / "main.py").write_text(
        "print('hello')\n",
        encoding="utf-8",
    )

    scanner = RepositoryScanner(tmp_path)
    chunker = CodeChunker(
        ChunkerConfig(max_lines=1, overlap_lines=0)
    )

    result = RepositoryIngestionPipeline(
        tmp_path,
        scanner=scanner,
        chunker=chunker,
    ).ingest()

    assert result.files_scanned == 1
    assert result.chunks_created == 1
    assert result.chunks[0].file_path == "main.py"
