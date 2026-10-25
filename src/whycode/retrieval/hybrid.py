"""Hybrid retrieval combining Lexical and Dense Vector search via Reciprocal Rank Fusion (RRF)."""

from __future__ import annotations

from dataclasses import dataclass

from whycode.ingest.chunker import CodeChunk
from whycode.retrieval.lexical import LexicalRetriever, RetrievalResult
from whycode.retrieval.vector import VectorRetriever


@dataclass(frozen=True, slots=True)
class FusionConfig:
    """Hyperparameters for Reciprocal Rank Fusion."""

    k: int = 60
    lexical_weight: float = 1.0
    vector_weight: float = 1.0

    def __post_init__(self) -> None:
        if self.k < 1:
            raise ValueError("RRF constant k must be at least 1.")
        if self.lexical_weight < 0 or self.vector_weight < 0:
            raise ValueError("Weights cannot be negative.")
        if self.lexical_weight == 0 and self.vector_weight == 0:
            raise ValueError("At least one weight must be positive.")


class HybridRetriever:
    """Fused retrieval combining lexical keyword scoring and dense vector similarity."""

    def __init__(
        self,
        lexical_retriever: LexicalRetriever,
        vector_retriever: VectorRetriever,
        config: FusionConfig | None = None,
    ) -> None:
        self.lexical_retriever = lexical_retriever
        self.vector_retriever = vector_retriever
        self.config = config or FusionConfig()

    def search(
        self,
        query: str,
        chunks: list[CodeChunk],
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        """Execute both lexical and vector searches and fuse rankings via RRF."""
        if top_k < 1:
            raise ValueError("top_k must be at least 1.")

        if not query or not query.strip():
            return []

        # Fetch candidate lists from each subsystem (oversampling candidate pool for fusion)
        candidate_k = max(top_k * 3, 20)

        lexical_results = (
            self.lexical_retriever.search(query=query, chunks=chunks, top_k=candidate_k)
            if self.config.lexical_weight > 0
            else []
        )

        vector_results = (
            self.vector_retriever.search(query=query, top_k=candidate_k)
            if self.config.vector_weight > 0
            else []
        )

        if not lexical_results and not vector_results:
            return []

        rrf_scores: dict[str, float] = {}
        chunk_map: dict[str, CodeChunk] = {}

        # Accumulate Lexical RRF scores
        if self.config.lexical_weight > 0:
            for rank, result in enumerate(lexical_results, start=1):
                chunk_id = result.chunk.chunk_id
                chunk_map[chunk_id] = result.chunk
                rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + (
                    self.config.lexical_weight / (self.config.k + rank)
                )

        # Accumulate Vector RRF scores
        if self.config.vector_weight > 0:
            for rank, result in enumerate(vector_results, start=1):
                chunk_id = result.chunk.chunk_id
                chunk_map[chunk_id] = result.chunk
                rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + (
                    self.config.vector_weight / (self.config.k + rank)
                )

        fused_results = [
            RetrievalResult(chunk=chunk_map[cid], score=score)
            for cid, score in rrf_scores.items()
        ]

        # Deterministic sorting: highest RRF score first, then file path, then start line
        fused_results.sort(
            key=lambda r: (-r.score, r.chunk.file_path, r.chunk.start_line)
        )

        return fused_results[:top_k]
