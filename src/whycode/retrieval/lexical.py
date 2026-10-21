
from __future__ import annotations

import re
from dataclasses import dataclass

from whycode.ingest.chunker import CodeChunk


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    chunk: CodeChunk
    score: float

    def __post_init__(self) -> None:
        if self.score <= 0:
            raise ValueError("Retrieval score must be positive.")


class LexicalRetriever:
    """Retrieve code chunks using keyword matching."""

    def search(
        self,
        query: str,
        chunks: list[CodeChunk],
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        if top_k < 1:
            raise ValueError("top_k must be at least 1.")

        if not query or not query.strip():
            return []

        query_tokens = self._expand_identifiers(
            self._tokenize(query)
        )

        if not query_tokens:
            return []

        query_terms = set(query_tokens)
        results: list[RetrievalResult] = []

        for chunk in chunks:
            content_tokens = self._expand_identifiers(
                self._tokenize(chunk.content)
            )
            content_terms = set(content_tokens)

            matched_terms = query_terms & content_terms

            if not matched_terms:
                continue

            # Reward chunks containing more occurrences of
            # the terms that the user searched for.
            score = (
                sum(
                    content_tokens.count(term)
                    for term in matched_terms
                )
                / len(query_terms)
            )

            results.append(
                RetrievalResult(
                    chunk=chunk,
                    score=score,
                )
            )

        # Sort by score first, then use stable tie-breakers.
        results.sort(
            key=lambda result: (
                -result.score,
                result.chunk.file_path,
                result.chunk.start_line,
            )
        )

        return results[:top_k]

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Extract case-insensitive identifiers and words."""
        return re.findall(
            r"[a-zA-Z_][a-zA-Z_0-9]*",
            text.lower(),
        )

    @staticmethod
    def _expand_identifiers(
        tokens: list[str],
    ) -> list[str]:
        """Preserve identifiers while also splitting snake_case."""
        expanded: list[str] = []

        for token in tokens:
            expanded.append(token)
            expanded.extend(
                part
                for part in token.split("_")
                if part
            )

        return expanded
