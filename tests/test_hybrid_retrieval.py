from pathlib import Path
import pytest

from whycode.ingest.chunker import CodeChunk
from whycode.llm.embedding import FakeEmbedder
from whycode.retrieval.hybrid import FusionConfig, HybridRetriever
from whycode.retrieval.index import VectorIndex
from whycode.retrieval.lexical import LexicalRetriever
from whycode.retrieval.service import CodebaseSearchService
from whycode.retrieval.vector import VectorRetriever


def _make_chunk(file_path: str, start_line: int, end_line: int, content: str) -> CodeChunk:
    return CodeChunk(
        chunk_id=f"{file_path}:{start_line}-{end_line}",
        file_path=file_path,
        start_line=start_line,
        end_line=end_line,
        content=content,
    )


def test_vector_retriever_finds_relevant_chunk(tmp_path: Path) -> None:
    index = VectorIndex(tmp_path / "index.db")
    embedder = FakeEmbedder(dimension=32)
    retriever = VectorRetriever(index=index, embedder=embedder)

    chunk = _make_chunk("cache.py", 1, 5, "class DiskCache: def get(): pass")
    emb = embedder.embed_texts([chunk.content])
    index.save_file_chunks("cache.py", "hash1", 1.0, [chunk], emb)

    results = retriever.search("DiskCache get", top_k=5)
    assert len(results) == 1
    assert results[0].chunk.file_path == "cache.py"
    assert results[0].score > 0


def test_hybrid_retriever_combines_lexical_and_vector_scores(tmp_path: Path) -> None:
    index = VectorIndex(tmp_path / "index.db")
    embedder = FakeEmbedder(dimension=32)
    lexical = LexicalRetriever()
    vector = VectorRetriever(index=index, embedder=embedder)
    hybrid = HybridRetriever(lexical_retriever=lexical, vector_retriever=vector)

    c1 = _make_chunk("auth/token.py", 1, 5, "def verify_jwt_token(token): return True")
    c2 = _make_chunk("db/session.py", 1, 5, "def open_db_session(): pass")

    chunks = [c1, c2]
    embs = embedder.embed_texts([c.content for c in chunks])
    index.save_file_chunks("auth/token.py", "h1", 1.0, [c1], [embs[0]])
    index.save_file_chunks("db/session.py", "h2", 1.0, [c2], [embs[1]])

    results = hybrid.search(query="verify jwt token", chunks=chunks, top_k=2)
    assert len(results) >= 1
    assert results[0].chunk.file_path == "auth/token.py"
    # Fused RRF score should be greater than zero
    assert results[0].score > 0


def test_hybrid_retriever_rejects_invalid_weights_or_k() -> None:
    with pytest.raises(ValueError, match="k must be at least 1"):
        FusionConfig(k=0)

    with pytest.raises(ValueError, match="negative"):
        FusionConfig(lexical_weight=-0.5)

    with pytest.raises(ValueError, match="positive"):
        FusionConfig(lexical_weight=0.0, vector_weight=0.0)


def test_search_service_with_hybrid_and_semantic_modes(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "math_ops.py").write_text(
        "def compute_factorial(n):\n    return 1 if n <= 1 else n * compute_factorial(n - 1)\n",
        encoding="utf-8",
    )

    embedder = FakeEmbedder(dimension=32)
    index = VectorIndex(tmp_path / "index.db")
    service = CodebaseSearchService(repo_path=repo, embedder=embedder, index=index)

    # Hybrid search
    hybrid_results = service.search("compute factorial", top_k=3, mode="hybrid")
    assert len(hybrid_results) == 1
    assert hybrid_results[0].chunk.file_path == "math_ops.py"

    # Semantic search
    semantic_results = service.search("compute factorial", top_k=3, mode="semantic")
    assert len(semantic_results) == 1
    assert semantic_results[0].chunk.file_path == "math_ops.py"

    # Lexical search
    lexical_results = service.search("compute factorial", top_k=3, mode="lexical")
    assert len(lexical_results) == 1
    assert lexical_results[0].chunk.file_path == "math_ops.py"


def test_search_service_rejects_semantic_without_embedder(tmp_path: Path) -> None:
    service = CodebaseSearchService(repo_path=tmp_path, embedder=None)
    with pytest.raises(ValueError, match="Vector retrieval requires an active embedder"):
        service.search("hello", mode="semantic")
