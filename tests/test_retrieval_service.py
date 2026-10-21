
from pathlib import Path

import pytest

from whycode.retrieval.service import CodebaseSearchService


def test_search_finds_relevant_source_code(tmp_path: Path) -> None:
    (tmp_path / "cache.py").write_text(
        "def build_cache_key():\n"
        "    cache_key = 'example'\n"
        "    return cache_key\n",
        encoding="utf-8",
    )

    (tmp_path / "page.py").write_text(
        "def render_page():\n"
        "    return 'hello'\n",
        encoding="utf-8",
    )

    service = CodebaseSearchService(tmp_path)
    results = service.search("cache key")

    assert len(results) == 1
    assert results[0].chunk.file_path == "cache.py"
    assert results[0].chunk.start_line == 1
    assert results[0].score > 0


def test_search_respects_top_k(tmp_path: Path) -> None:
    (tmp_path / "first.py").write_text(
        "cache = 'first'\n",
        encoding="utf-8",
    )
    (tmp_path / "second.py").write_text(
        "cache = 'second'\n",
        encoding="utf-8",
    )

    service = CodebaseSearchService(tmp_path)
    results = service.search("cache", top_k=1)

    assert len(results) == 1


def test_search_returns_empty_for_blank_query(tmp_path: Path) -> None:
    service = CodebaseSearchService(tmp_path)

    assert service.search("") == []
    assert service.search("   ") == []


def test_search_rejects_invalid_top_k(tmp_path: Path) -> None:
    service = CodebaseSearchService(tmp_path)

    with pytest.raises(ValueError, match="top_k must be at least 1"):
        service.search("cache", top_k=0)
