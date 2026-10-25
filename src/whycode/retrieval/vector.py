"""Dense vector retrieval engine using embeddings and persistent VectorIndex."""

from __future__ import annotations

from whycode.llm.embedding import BaseEmbedder
from whycode.retrieval.index import VectorIndex
from whycode.retrieval.lexical import RetrievalResult


class VectorRetriever:
    """Retrieve code chunks using semantic vector cosine similarity."""

    def __init__(self, index: VectorIndex, embedder: BaseEmbedder) -> None:
        self.index = index
        self.embedder = embedder

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        """Search the persistent vector index with an embedded query string."""
        if top_k < 1:
            raise ValueError("top_k must be at least 1.")

        if not query or not query.strip():
            return []

        query_vector = self.embedder.embed_query(query)
        return self.index.vector_search(query_vector=query_vector, top_k=top_k)
