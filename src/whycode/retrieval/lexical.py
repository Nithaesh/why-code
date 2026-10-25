
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
    """Retrieve code chunks using keyword matching and definition signals."""

    STOPWORDS = {
        "a", "an", "and", "are", "as", "at", "be", "by",
        "does", "do", "for", "from", "how", "in", "is",
        "it", "of", "on", "or", "the", "this", "to",
        "was", "were", "what", "when", "where", "which",
        "who", "why", "with", "work", "project",
    }

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

        query_tokens = self._expand_text_identifiers(query)
        query_terms = {
            term for term in query_tokens
            if term not in self.STOPWORDS
        }

        if not query_terms:
            return []

        query_identifiers = set(self._tokenize(query))
        implementation_intent = bool(
            query_identifiers
            & {"implementation", "implement", "implemented"}
        )

        results: list[RetrievalResult] = []

        for chunk in chunks:
            content_tokens = self._expand_text_identifiers(chunk.content)
            content_terms = set(content_tokens)
            matched_terms = query_terms & content_terms

            if not matched_terms:
                continue

            # Reward both distinct matches and limited repetition.
            score = (
                len(matched_terms) / len(query_terms)
                + 0.1 * sum(
                    min(content_tokens.count(term), 5)
                    for term in matched_terms
                )
            )

            normalized_path = chunk.file_path.replace("\\", "/").lower()
            path_tokens = set(
                self._expand_text_identifiers(normalized_path)
            )
            path_matches = query_terms & path_tokens

            # File paths provide useful relevance evidence.
            score += 0.5 * len(path_matches)

            # Prefer a module whose filename exactly matches a query term.
            file_name = normalized_path.rsplit("/", 1)[-1]
            file_stem = file_name.rsplit(".", 1)[0]

            if file_stem in query_terms:
                score += 1.0


            is_test_file = (
                normalized_path.startswith("tests/")
                or "/tests/" in normalized_path
                or normalized_path.startswith("test_")
                or "/test_" in normalized_path
            )
            if is_test_file:
                score -= 1.0

            # Prefer production code for explicit implementation queries.
            if implementation_intent and not is_test_file:
                score += 2.0
            # Reward the strongest matching definition once per chunk.
            definition_bonus = 0.0

            for line in chunk.content.splitlines():
                class_match = re.match(
                    r"^\s*class\s+([A-Za-z_]\w*)",
                    line,
                )
                function_match = re.match(
                    r"^\s*(?:async\s+)?def\s+([A-Za-z_]\w*)",
                    line,
                )

                if class_match:
                    defined_name = class_match.group(1)
                elif function_match:
                    defined_name = function_match.group(1)
                else:
                    continue

                # Split CamelCase before lowercasing.
                split_name = re.sub(
                    r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])",
                    " ",
                    defined_name,
                )

                definition_terms = set(
                    self._expand_text_identifiers(split_name)
                )

                if defined_name.lower() in query_identifiers:
                    definition_bonus = 5.0
                    break
                elif (
                    definition_terms & query_terms
                    and not defined_name.lower().startswith("test_")
                ):
                    definition_bonus = max(definition_bonus, 2.0)

            score += definition_bonus


            # Skip chunks whose penalties reduce their score to zero or below.
            if score <= 0:
                continue
            results.append(
                RetrievalResult(chunk=chunk, score=score)
            )
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
    def _normalize_word(token: str) -> str:
        """Normalize common suffixes without altering identifiers."""
        if "_" in token or any(char.isdigit() for char in token):
            return token

        if len(token) > 5 and token.endswith("ing"):
            base = token[:-3]

            if len(base) >= 2 and base[-1] == base[-2]:
                base = base[:-1]

            if base.endswith("ch"):
                return base + "e"

            return base

        if len(token) > 4 and token.endswith("ed"):
            base = token[:-2]

            if base.endswith("ch"):
                return base + "e"

            return base

        if len(token) > 4 and token.endswith("es"):
            base = token[:-2]

            if base.endswith(("s", "x", "z", "ch", "sh")):
                return base + "e"

            return base

        if len(token) > 4 and token.endswith("s"):
            return token[:-1]

        return token

    @classmethod
    def _expand_identifiers(
        cls,
        tokens: list[str],
    ) -> list[str]:
        """Preserve identifiers and expand snake_case components."""
        expanded: list[str] = []

        for token in tokens:
            expanded.append(token)

            for part in token.split("_"):
                if part:
                    expanded.append(cls._normalize_word(part))

        return expanded

    @classmethod
    def _expand_text_identifiers(cls, text: str) -> list[str]:
        """Expand snake_case and CamelCase into searchable terms."""
        camel_split = re.sub(
            r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])",
            " ",
            text,
        )

        original_tokens = cls._expand_identifiers(cls._tokenize(text))
        split_tokens = cls._expand_identifiers(
            cls._tokenize(camel_split)
        )

        return original_tokens + split_tokens
