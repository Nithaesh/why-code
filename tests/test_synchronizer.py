from pathlib import Path
from unittest.mock import MagicMock

from whycode.llm.embedding import FakeEmbedder
from whycode.retrieval.index import VectorIndex
from whycode.retrieval.sync import IndexSynchronizer


def test_sync_indexes_new_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "hello.py").write_text("def greet(): return 'hi'\n", encoding="utf-8")

    index = VectorIndex(tmp_path / "index.db")
    embedder = FakeEmbedder(dimension=16)
    synchronizer = IndexSynchronizer(repo, index, embedder)

    stats = synchronizer.sync()
    assert stats.added_files == 1
    assert stats.modified_files == 0
    assert stats.deleted_files == 0
    assert stats.unchanged_files == 0
    assert stats.total_chunks == 1
    assert "hello.py" in index.get_indexed_files()


def test_sync_skips_unchanged_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "hello.py").write_text("def greet(): return 'hi'\n", encoding="utf-8")

    index = VectorIndex(tmp_path / "index.db")
    fake = FakeEmbedder(dimension=16)
    mock_embedder = MagicMock(wraps=fake)
    synchronizer = IndexSynchronizer(repo, index, mock_embedder)

    # First sync: indexes the file
    stats1 = synchronizer.sync()
    assert stats1.added_files == 1
    assert mock_embedder.embed_texts.call_count == 1

    # Second sync: unchanged, should skip embedding entirely
    stats2 = synchronizer.sync()
    assert stats2.added_files == 0
    assert stats2.modified_files == 0
    assert stats2.unchanged_files == 1
    assert stats2.total_chunks == 1
    # embed_texts was NOT called again
    assert mock_embedder.embed_texts.call_count == 1


def test_sync_reindexes_modified_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    file_path = repo / "hello.py"
    file_path.write_text("def greet(): return 'hi'\n", encoding="utf-8")

    index = VectorIndex(tmp_path / "index.db")
    embedder = FakeEmbedder(dimension=16)
    synchronizer = IndexSynchronizer(repo, index, embedder)

    synchronizer.sync()
    assert index.get_all_chunks()[0].content == "def greet(): return 'hi'"

    # Modify file content
    file_path.write_text("def greet(): return 'hello world'\n", encoding="utf-8")

    stats = synchronizer.sync()
    assert stats.added_files == 0
    assert stats.modified_files == 1
    assert stats.unchanged_files == 0
    assert index.get_all_chunks()[0].content == "def greet(): return 'hello world'"


def test_sync_deletes_stale_files_from_index(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    f1 = repo / "file1.py"
    f2 = repo / "file2.py"
    f1.write_text("def func1(): pass\n", encoding="utf-8")
    f2.write_text("def func2(): pass\n", encoding="utf-8")

    index = VectorIndex(tmp_path / "index.db")
    embedder = FakeEmbedder(dimension=16)
    synchronizer = IndexSynchronizer(repo, index, embedder)

    synchronizer.sync()
    assert index.count_chunks() == 2

    # Remove f2 from filesystem
    f2.unlink()

    stats = synchronizer.sync()
    assert stats.deleted_files == 1
    assert stats.unchanged_files == 1
    assert index.count_chunks() == 1
    assert "file2.py" not in index.get_indexed_files()
    assert "file1.py" in index.get_indexed_files()


def test_sync_force_rebuilds_index(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "file.py").write_text("code = 1\n", encoding="utf-8")

    index = VectorIndex(tmp_path / "index.db")
    embedder = FakeEmbedder(dimension=16)
    synchronizer = IndexSynchronizer(repo, index, embedder)

    synchronizer.sync()
    # Force rebuild
    stats = synchronizer.sync(force=True)
    assert stats.added_files == 1
    assert stats.unchanged_files == 0
    assert stats.total_chunks == 1
