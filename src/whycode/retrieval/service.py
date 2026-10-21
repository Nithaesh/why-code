
from __future__ import annotations

from pathlib import Path

from whycode.ingest.pipeline import RepositoryIngestionPipeline
from whycode.retrieval.lexical import (
    LexicalRetriever,
    RetrievalResult,
)


class CodebaseSearchService:
    """Search a repository's source code using lexical retrieval."""

    def __init__(self, repo_path: str | Path) -> None:
        self.pipeline = RepositoryIngestionPipeline(repo_path)
        self.retriever = LexicalRetriever()

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        """Return the most relevant code chunks for a query."""

        if top_k < 1:
            raise ValueError("top_k must be at least 1.")

        if not query or not query.strip():
            return []

        ingestion_result = self.pipeline.ingest()

        return self.retriever.search(
            query=query,
            chunks=list(ingestion_result.chunks),
            top_k=top_k,
        )
