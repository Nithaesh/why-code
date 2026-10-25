from pathlib import Path

from eval.eval_retrieval import (
    BenchmarkQuery,
    compute_hit_at_k,
    compute_mrr,
    evaluate_mode,
    load_benchmark,
)
from whycode.ingest.chunker import CodeChunk
from whycode.llm.embedding import FakeEmbedder
from whycode.retrieval.index import VectorIndex
from whycode.retrieval.lexical import RetrievalResult
from whycode.retrieval.service import CodebaseSearchService


def _make_result(file_path: str, score: float = 1.0) -> RetrievalResult:
    chunk = CodeChunk(
        chunk_id=f"{file_path}:1-5",
        file_path=file_path,
        start_line=1,
        end_line=5,
        content="some code",
    )
    return RetrievalResult(chunk=chunk, score=score)


def test_compute_hit_at_k() -> None:
    results = [
        _make_result("src/a.py"),
        _make_result("src/b.py"),
        _make_result("src/c.py"),
    ]

    assert compute_hit_at_k(results, "src/a.py", k=1) == 1.0
    assert compute_hit_at_k(results, "src/b.py", k=1) == 0.0
    assert compute_hit_at_k(results, "src/b.py", k=2) == 1.0
    assert compute_hit_at_k(results, "src/missing.py", k=3) == 0.0


def test_compute_mrr() -> None:
    results = [
        _make_result("src/first.py"),
        _make_result("src/second.py"),
        _make_result("src/third.py"),
    ]

    assert compute_mrr(results, "src/first.py") == 1.0
    assert compute_mrr(results, "src/second.py") == 0.5
    assert compute_mrr(results, "src/third.py") == 1.0 / 3.0
    assert compute_mrr(results, "src/not_present.py") == 0.0


def test_load_benchmark_parses_json(tmp_path: Path) -> None:
    data_file = tmp_path / "queries.json"
    data_file.write_text(
        '{"queries": [{"id": "t1", "query": "auth", "category": "test", "expected_file": "a.py"}]}',
        encoding="utf-8",
    )
    benchmark = load_benchmark(data_file)
    assert len(benchmark) == 1
    assert benchmark[0].id == "t1"
    assert benchmark[0].query == "auth"
    assert benchmark[0].expected_file == "a.py"


def test_evaluation_runs_on_synthetic_repository(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "cache.py").write_text("class DiskCache:\n    def get(): pass\n", encoding="utf-8")
    (repo / "scanner.py").write_text("class RepositoryScanner:\n    def scan(): pass\n", encoding="utf-8")

    benchmark = [
        BenchmarkQuery(
            id="1",
            query="DiskCache",
            category="id",
            expected_file="cache.py",
        ),
        BenchmarkQuery(
            id="2",
            query="RepositoryScanner",
            category="id",
            expected_file="scanner.py",
        ),
    ]

    embedder = FakeEmbedder(dimension=32)
    index = VectorIndex(tmp_path / "index.db")
    service = CodebaseSearchService(repo_path=repo, embedder=embedder, index=index)
    service.sync(force=True)

    summary = evaluate_mode(service, benchmark, mode="hybrid", top_k=3)
    assert summary.total_queries == 2
    assert summary.hit_at_3 == 1.0
    assert summary.mrr == 1.0
