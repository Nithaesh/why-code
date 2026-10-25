from pathlib import Path
import pytest

from whycode.ingest.chunker import CodeChunk
from whycode.retrieval.index import VectorIndex


def _make_chunk(file_path: str, start_line: int, end_line: int, content: str) -> CodeChunk:
    chunk_id = f"{file_path}:{start_line}-{end_line}"
    return CodeChunk(
        chunk_id=chunk_id,
        file_path=file_path,
        start_line=start_line,
        end_line=end_line,
        content=content,
    )


def test_index_initializes_tables(tmp_path: Path) -> None:
    db_file = tmp_path / "test_index.db"
    index = VectorIndex(db_file)
    assert db_file.exists()
    assert index.count_chunks() == 0
    assert index.get_indexed_files() == {}


def test_index_saves_and_retrieves_chunks(tmp_path: Path) -> None:
    index = VectorIndex(tmp_path / "index.db")
    chunk1 = _make_chunk("auth.py", 1, 10, "def login(): pass")
    chunk2 = _make_chunk("auth.py", 11, 20, "def logout(): pass")
    emb1 = [1.0, 0.0]
    emb2 = [0.0, 1.0]

    index.save_file_chunks(
        file_path="auth.py",
        content_hash="hash_v1",
        mtime=1000.0,
        chunks=[chunk1, chunk2],
        embeddings=[emb1, emb2],
    )

    assert index.count_chunks() == 2
    indexed_files = index.get_indexed_files()
    assert indexed_files == {"auth.py": "hash_v1"}

    all_chunks = index.get_all_chunks()
    assert len(all_chunks) == 2
    assert all_chunks[0].chunk_id == chunk1.chunk_id
    assert all_chunks[1].chunk_id == chunk2.chunk_id


def test_index_updates_file_chunks_atomically(tmp_path: Path) -> None:
    index = VectorIndex(tmp_path / "index.db")
    chunk_v1 = _make_chunk("main.py", 1, 5, "print('hello v1')")
    index.save_file_chunks(
        file_path="main.py",
        content_hash="hash_1",
        mtime=1.0,
        chunks=[chunk_v1],
        embeddings=[[1.0, 0.0]],
    )
    assert index.count_chunks() == 1

    # Update file with 2 new chunks
    chunk_v2_a = _make_chunk("main.py", 1, 5, "print('hello v2')")
    chunk_v2_b = _make_chunk("main.py", 6, 10, "print('world v2')")
    index.save_file_chunks(
        file_path="main.py",
        content_hash="hash_2",
        mtime=2.0,
        chunks=[chunk_v2_a, chunk_v2_b],
        embeddings=[[0.0, 1.0], [0.5, 0.5]],
    )

    assert index.count_chunks() == 2
    assert index.get_indexed_files()["main.py"] == "hash_2"
    all_chunks = index.get_all_chunks()
    assert [c.content for c in all_chunks] == ["print('hello v2')", "print('world v2')"]


def test_index_deletes_file_and_associated_chunks(tmp_path: Path) -> None:
    index = VectorIndex(tmp_path / "index.db")
    c1 = _make_chunk("a.py", 1, 5, "code a")
    c2 = _make_chunk("b.py", 1, 5, "code b")

    index.save_file_chunks("a.py", "hash_a", 1.0, [c1], [[1.0, 0.0]])
    index.save_file_chunks("b.py", "hash_b", 1.0, [c2], [[0.0, 1.0]])
    assert index.count_chunks() == 2

    index.delete_file("a.py")
    assert index.count_chunks() == 1
    assert "a.py" not in index.get_indexed_files()
    assert "b.py" in index.get_indexed_files()


def test_index_vector_search_ranks_by_cosine_similarity(tmp_path: Path) -> None:
    index = VectorIndex(tmp_path / "index.db")
    c_exact = _make_chunk("math.py", 1, 5, "def calculate_sum(): pass")
    c_ortho = _make_chunk("other.py", 1, 5, "def unrelated(): pass")

    # c_exact has vector [1.0, 0.0], c_ortho has vector [0.0, 1.0]
    index.save_file_chunks("math.py", "h1", 1.0, [c_exact], [[1.0, 0.0]])
    index.save_file_chunks("other.py", "h2", 1.0, [c_ortho], [[0.0, 1.0]])

    # Query vector is [1.0, 0.0]
    results = index.vector_search(query_vector=[1.0, 0.0], top_k=5)
    assert len(results) == 1  # Only positive similarity returned
    assert results[0].chunk.file_path == "math.py"
    assert abs(results[0].score - 1.0) < 1e-5


def test_index_clear_empties_all_tables(tmp_path: Path) -> None:
    index = VectorIndex(tmp_path / "index.db")
    chunk = _make_chunk("demo.py", 1, 3, "val = 10")
    index.save_file_chunks("demo.py", "h", 1.0, [chunk], [[1.0]])
    assert index.count_chunks() == 1

    index.clear()
    assert index.count_chunks() == 0
    assert index.get_indexed_files() == {}


def test_index_rejects_mismatched_chunks_and_embeddings(tmp_path: Path) -> None:
    index = VectorIndex(tmp_path / "index.db")
    chunk = _make_chunk("demo.py", 1, 3, "val = 10")

    with pytest.raises(ValueError, match="Mismatch"):
        index.save_file_chunks("demo.py", "h", 1.0, [chunk], [])
