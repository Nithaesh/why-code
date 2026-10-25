"""Embedding provider contracts and implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
import hashlib
import json
import logging
from pathlib import Path
import time
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class BaseEmbedder(ABC):
    """Provider-independent interface for dense vector embeddings."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Vector dimension produced by this embedder."""
        raise NotImplementedError

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Compute dense vector embeddings for a list of document strings."""
        raise NotImplementedError

    def embed_query(self, text: str) -> list[float]:
        """Compute dense vector embedding for a single query string."""
        if not text or not text.strip():
            # Return a zero vector for empty query strings
            return [0.0] * self.dimension
        results = self.embed_texts([text])
        return results[0]


class FakeEmbedder(BaseEmbedder):
    """Deterministic, offline pseudo-embedder for reproducible testing.

    Generates normalized dense vectors from character n-grams and token hashes
    without calling any external network service.
    """

    def __init__(self, dimension: int = 64) -> None:
        if dimension <= 0:
            raise ValueError("dimension must be positive.")
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def _embed_single(self, text: str) -> list[float]:
        if not text or not text.strip():
            return [0.0] * self._dimension

        vec = np.zeros(self._dimension, dtype=np.float32)
        tokens = text.lower().split()
        for token in tokens:
            # Hash tokens into coordinate buckets
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:4], "big") % self._dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vec[bucket] += sign

        # Add 3-gram character frequency signal
        cleaned = text.lower().replace("\n", " ")
        for i in range(max(0, len(cleaned) - 2)):
            tri = cleaned[i : i + 3]
            digest = hashlib.md5(tri.encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:2], "big") % self._dimension
            vec[bucket] += 0.5

        norm = float(np.linalg.norm(vec))
        if norm > 1e-9:
            vec = vec / norm
        return vec.tolist()

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_single(t) for t in texts]


def _is_rate_limit_error(error: Exception) -> bool:
    status = getattr(error, "status_code", None)
    if status is None:
        status = getattr(error, "code", None)
    if status == 429 or str(status) == "429":
        return True
    return "429" in str(error) and any(
        w in str(error).lower() for w in ("rate", "quota", "resource exhausted")
    )


import re

class GeminiEmbedder(BaseEmbedder):
    """Compute embeddings using Google's GenAI SDK (e.g. gemini-embedding-001)."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-embedding-001",
        dimension: int = 3072,
        batch_size: int = 8,
    ) -> None:
        from google import genai

        self.model = model
        self._dimension = dimension
        self.batch_size = max(1, batch_size)
        self.client = genai.Client(api_key=api_key)

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        all_embeddings: list[list[float]] = []

        for i in range(0, len(texts), self.batch_size):
            if i > 0:
                time.sleep(0.5)
            batch = texts[i : i + self.batch_size]
            batch_result = self._embed_batch_with_retry(batch)
            all_embeddings.extend(batch_result)

        return all_embeddings

    def _embed_batch_with_retry(self, batch: list[str]) -> list[list[float]]:
        for attempt in range(5):
            try:
                response = self.client.models.embed_content(
                    model=self.model,
                    contents=batch,
                )
                embeddings_data = getattr(response, "embeddings", None)
                if not embeddings_data:
                    raise RuntimeError("Gemini returned no embeddings.")

                results: list[list[float]] = []
                for item in embeddings_data:
                    values = getattr(item, "values", None)
                    if values is None:
                        raise RuntimeError("Embedding item has no values.")
                    arr = np.array(values, dtype=np.float32)
                    norm = float(np.linalg.norm(arr))
                    if norm > 1e-9:
                        arr = arr / norm
                    results.append(arr.tolist())
                return results

            except Exception as exc:
                if _is_rate_limit_error(exc) and attempt < 4:
                    # Check for explicit retryDelay from Google API
                    delay_match = re.search(r"retry\s+in\s+([0-9.]+)\s*s", str(exc), re.IGNORECASE)
                    if delay_match:
                        delay = float(delay_match.group(1)) + 1.0
                    else:
                        delay = max(5.0, float(2 ** (attempt + 2)))
                    logger.warning(
                        "Gemini embedding rate limit (429); waiting %.1f seconds before retry %d/4.",
                        delay,
                        attempt + 1,
                    )
                    time.sleep(delay)
                    continue
                if _is_rate_limit_error(exc):
                    raise RuntimeError(
                        "Gemini embedding rate limit persisted after retries."
                    ) from exc
                raise RuntimeError(
                    f"Gemini embedding request failed: {exc}"
                ) from exc

        raise RuntimeError("Gemini embedding request failed after retries.")


class CachedEmbedder(BaseEmbedder):
    """Disk-backed caching wrapper for any BaseEmbedder.

    Avoids re-computing embeddings for identical text snippets.
    """

    def __init__(
        self,
        embedder: BaseEmbedder,
        cache_dir: Path | str,
        provider_name: str = "gemini",
        model_name: str = "text-embedding-004",
    ) -> None:
        self.embedder = embedder
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.provider_name = provider_name
        self.model_name = model_name

    @property
    def dimension(self) -> int:
        return self.embedder.dimension

    def _make_key(self, text: str) -> str:
        payload = f"{self.provider_name}:{self.model_name}:{text}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        cached_results: dict[int, list[float]] = {}
        missing_indices: list[int] = []
        missing_texts: list[str] = []

        for idx, text in enumerate(texts):
            key = self._make_key(text)
            cache_file = self.cache_dir / f"emb_{key}.json"
            if cache_file.exists():
                try:
                    vec = json.loads(cache_file.read_text(encoding="utf-8"))
                    cached_results[idx] = vec
                    continue
                except (OSError, json.JSONDecodeError):
                    pass
            missing_indices.append(idx)
            missing_texts.append(text)

        if missing_texts:
            new_embeddings = self.embedder.embed_texts(missing_texts)
            for idx, text, emb in zip(missing_indices, missing_texts, new_embeddings):
                cached_results[idx] = emb
                key = self._make_key(text)
                cache_file = self.cache_dir / f"emb_{key}.json"
                tmp_file = self.cache_dir / f"emb_{key}.tmp"
                try:
                    tmp_file.write_text(json.dumps(emb), encoding="utf-8")
                    tmp_file.replace(cache_file)
                except OSError:
                    logger.warning("Could not persist embedding cache entry.")

        return [cached_results[i] for i in range(len(texts))]
