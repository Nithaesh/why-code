from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from whycode.config import Settings
from whycode.ingest.chunker import CodeChunker
from whycode.ingest.pipeline import RepositoryIngestionPipeline
from whycode.ingest.scanner import RepositoryScanner
from whycode.llm.embedding import BaseEmbedder
from whycode.retrieval.hybrid import HybridRetriever
from whycode.retrieval.index import VectorIndex
from whycode.retrieval.lexical import LexicalRetriever, RetrievalResult
from whycode.retrieval.sync import IndexSynchronizer, SyncStats
from whycode.retrieval.vector import VectorRetriever

logger = logging.getLogger(__name__)


class CodebaseSearchService:
    """Search a repository's source code using lexical, semantic, or persistent hybrid retrieval."""

    def __init__(
        self,
        repo_path: str | Path,
        embedder: BaseEmbedder | None = None,
        index: VectorIndex | None = None,
        scanner: RepositoryScanner | None = None,
        chunker: CodeChunker | None = None,
    ) -> None:
        self.repo_path = Path(repo_path).expanduser().resolve()
        self.scanner = scanner or RepositoryScanner(self.repo_path)
        self.chunker = chunker or CodeChunker()
        self.lexical_retriever = LexicalRetriever()

        # Ephemeral ingestion pipeline for fast, zero-configuration lexical search
        self.pipeline = RepositoryIngestionPipeline(
            self.repo_path, scanner=self.scanner, chunker=self.chunker
        )

        self.embedder = embedder
        self.index = index

        if self.embedder is not None:
            if self.index is None:
                settings = Settings()
                repo_hash = hashlib.sha256(str(self.repo_path).encode("utf-8")).hexdigest()[:12]
                db_path = settings.whycode_index_dir / f"repo_{repo_hash}.db"
                self.index = VectorIndex(db_path)

            self.synchronizer: IndexSynchronizer | None = IndexSynchronizer(
                repo_path=self.repo_path,
                index=self.index,
                embedder=self.embedder,
                scanner=self.scanner,
                chunker=self.chunker,
            )
            self.vector_retriever: VectorRetriever | None = VectorRetriever(
                index=self.index,
                embedder=self.embedder,
            )
            self.hybrid_retriever: HybridRetriever | None = HybridRetriever(
                lexical_retriever=self.lexical_retriever,
                vector_retriever=self.vector_retriever,
            )
        else:
            self.synchronizer = None
            self.vector_retriever = None
            self.hybrid_retriever = None

    def sync(self, force: bool = False) -> SyncStats | None:
        """Synchronize the repository files with the persistent vector index."""
        if self.synchronizer is not None:
            return self.synchronizer.sync(force=force)
        return None

    def search(
        self,
        query: str,
        top_k: int = 5,
        mode: str = "hybrid",
        force_sync: bool = False,
    ) -> list[RetrievalResult]:
        """Return the most relevant code chunks using the requested retrieval mode."""
        if top_k < 1:
            raise ValueError("top_k must be at least 1.")

        if not query or not query.strip():
            return []

        # If an embedder and index are configured, use persistent hybrid/vector search
        if self.embedder is not None and self.index is not None and self.synchronizer is not None:
            self.synchronizer.sync(force=force_sync)
            all_chunks = self.index.get_all_chunks()

            if mode == "lexical":
                return self.lexical_retriever.search(
                    query=query, chunks=all_chunks, top_k=top_k
                )

            if mode in ("vector", "semantic"):
                if self.vector_retriever is not None:
                    return self.vector_retriever.search(query=query, top_k=top_k)
                raise ValueError("Vector retrieval requires an active vector retriever.")

            if mode == "hybrid":
                if self.hybrid_retriever is not None:
                    return self.hybrid_retriever.search(
                        query=query, chunks=all_chunks, top_k=top_k
                    )
                return self.lexical_retriever.search(
                    query=query, chunks=all_chunks, top_k=top_k
                )

            raise ValueError(f"Unknown retrieval mode: {mode}")

        # When no embedder is configured (e.g. lightweight unit tests), execute lexical search
        if mode in ("vector", "semantic"):
            raise ValueError("Vector retrieval requires an active embedder.")

        ingestion_result = self.pipeline.ingest()
        return self.lexical_retriever.search(
            query=query,
            chunks=list(ingestion_result.chunks),
            top_k=top_k,
        )
