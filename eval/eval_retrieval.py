"""Retrieval evaluation harness calculating Hit@K and Mean Reciprocal Rank (MRR)."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import time
from typing import Sequence

from whycode.llm.embedding import BaseEmbedder, FakeEmbedder
from whycode.retrieval.index import VectorIndex
from whycode.retrieval.lexical import RetrievalResult
from whycode.retrieval.service import CodebaseSearchService


@dataclass(frozen=True, slots=True)
class BenchmarkQuery:
    id: str
    query: str
    category: str
    expected_file: str


@dataclass(frozen=True, slots=True)
class MetricSummary:
    mode: str
    total_queries: int
    hit_at_1: float
    hit_at_3: float
    hit_at_5: float
    mrr: float
    avg_latency_ms: float


def compute_hit_at_k(results: Sequence[RetrievalResult], expected_file: str, k: int) -> float:
    """Return 1.0 if the expected file appears in the top-k results, else 0.0."""
    norm_expected = expected_file.replace("\\", "/").lower()
    for res in results[:k]:
        norm_actual = res.chunk.file_path.replace("\\", "/").lower()
        if norm_actual == norm_expected:
            return 1.0
    return 0.0


def compute_mrr(results: Sequence[RetrievalResult], expected_file: str) -> float:
    """Return the reciprocal rank (1/rank) of the first relevant chunk."""
    norm_expected = expected_file.replace("\\", "/").lower()
    for rank, res in enumerate(results, start=1):
        norm_actual = res.chunk.file_path.replace("\\", "/").lower()
        if norm_actual == norm_expected:
            return 1.0 / rank
    return 0.0


def load_benchmark(data_path: Path | str) -> list[BenchmarkQuery]:
    path = Path(data_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        BenchmarkQuery(
            id=item["id"],
            query=item["query"],
            category=item["category"],
            expected_file=item["expected_file"],
        )
        for item in data["queries"]
    ]


def evaluate_mode(
    service: CodebaseSearchService,
    benchmark: list[BenchmarkQuery],
    mode: str,
    top_k: int = 5,
) -> MetricSummary:
    hit_1_list: list[float] = []
    hit_3_list: list[float] = []
    hit_5_list: list[float] = []
    mrr_list: list[float] = []
    latencies: list[float] = []

    for bq in benchmark:
        start = time.perf_counter()
        results = service.search(query=bq.query, top_k=top_k, mode=mode)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        latencies.append(elapsed_ms)

        hit_1_list.append(compute_hit_at_k(results, bq.expected_file, k=1))
        hit_3_list.append(compute_hit_at_k(results, bq.expected_file, k=3))
        hit_5_list.append(compute_hit_at_k(results, bq.expected_file, k=5))
        mrr_list.append(compute_mrr(results, bq.expected_file))

    n = len(benchmark)
    return MetricSummary(
        mode=mode,
        total_queries=n,
        hit_at_1=sum(hit_1_list) / n if n else 0.0,
        hit_at_3=sum(hit_3_list) / n if n else 0.0,
        hit_at_5=sum(hit_5_list) / n if n else 0.0,
        mrr=sum(mrr_list) / n if n else 0.0,
        avg_latency_ms=sum(latencies) / n if n else 0.0,
    )


def run_benchmark(
    repo_path: Path,
    benchmark_path: Path,
    embedder: BaseEmbedder | None = None,
) -> list[MetricSummary]:
    benchmark = load_benchmark(benchmark_path)
    embedder = embedder or FakeEmbedder(dimension=64)
    index_db = repo_path / ".whycode_index" / "eval_index.db"
    index = VectorIndex(index_db)
    service = CodebaseSearchService(repo_path, embedder=embedder, index=index)
    service.sync(force=True)

    summaries = []
    for mode in ["lexical", "semantic", "hybrid"]:
        summary = evaluate_mode(service, benchmark, mode=mode, top_k=5)
        summaries.append(summary)

    return summaries


def main() -> None:
    parser = argparse.ArgumentParser(description="Run WhyCode retrieval evaluation benchmark.")
    parser.add_argument("--repo", default=".", help="Path to repository")
    parser.add_argument(
        "--data",
        default="eval/benchmark_data.json",
        help="Path to benchmark JSON dataset",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Use real GeminiEmbedder with local cache instead of FakeEmbedder",
    )
    args = parser.parse_args()

    repo_path = Path(args.repo).resolve()
    benchmark_path = Path(args.data).resolve()

    embedder: BaseEmbedder | None = None
    if args.live:
        from whycode.config import Settings
        from whycode.llm.embedding import CachedEmbedder, GeminiEmbedder

        settings = Settings()
        api_key = settings.require_gemini_key()
        raw = GeminiEmbedder(api_key=api_key, model=settings.gemini_embedding_model)
        embedder = CachedEmbedder(
            embedder=raw,
            cache_dir=settings.whycode_cache_dir,
            provider_name="gemini",
            model_name=settings.gemini_embedding_model,
        )

    print(f"\n--- Running Retrieval Evaluation on {repo_path.name} (live={args.live}) ---")
    summaries = run_benchmark(repo_path, benchmark_path, embedder=embedder)

    print(f"{'Mode':<12} | {'Hit@1':<8} | {'Hit@3':<8} | {'Hit@5':<8} | {'MRR':<8} | {'Avg Latency (ms)':<16}")
    print("-" * 72)
    for s in summaries:
        print(
            f"{s.mode:<12} | {s.hit_at_1 * 100:>6.1f}% | {s.hit_at_3 * 100:>6.1f}% | "
            f"{s.hit_at_5 * 100:>6.1f}% | {s.mrr:>8.3f} | {s.avg_latency_ms:>16.2f}"
        )


if __name__ == "__main__":
    main()
