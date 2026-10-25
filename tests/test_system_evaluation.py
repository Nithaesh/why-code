"""Tests for the system evaluation harness."""

from pathlib import Path
from eval.eval_system import compute_hit_at_k, compute_mrr, run_system_evaluation
from whycode.ingest.chunker import CodeChunk
from whycode.retrieval.lexical import RetrievalResult


def test_metric_computations():
    chunk1 = CodeChunk("c1", "src/whycode/cache.py", 1, 10, "content 1")
    chunk2 = CodeChunk("c2", "src/whycode/scanner.py", 1, 10, "content 2")
    results = [RetrievalResult(chunk1, 0.9), RetrievalResult(chunk2, 0.8)]

    # Hit@1 for cache.py -> 1.0
    assert compute_hit_at_k(results, "src/whycode/cache.py", 1) == 1.0
    # Hit@1 for scanner.py -> 0.0 (it is at rank 2)
    assert compute_hit_at_k(results, "src/whycode/scanner.py", 1) == 0.0
    # Hit@2 for scanner.py -> 1.0
    assert compute_hit_at_k(results, "src/whycode/scanner.py", 2) == 1.0

    # MRR computations
    assert compute_mrr(results, "src/whycode/cache.py") == 1.0
    assert compute_mrr(results, "src/whycode/scanner.py") == 0.5
    assert compute_mrr(results, "src/whycode/missing.py") == 0.0


def test_system_evaluation_run(tmp_path: Path):
    # Execute system evaluation over current workspace
    workspace = Path(__file__).resolve().parents[1]
    output_file = tmp_path / "system_benchmark.json"

    report = run_system_evaluation(workspace, output_file)
    assert report["status"] == "PASSED"
    assert "retrieval_performance" in report
    assert "citation_verification" in report
    assert "agentic_investigation" in report
    assert output_file.exists()
