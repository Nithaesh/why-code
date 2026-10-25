from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest

from whycode.llm.embedding import (
    BaseEmbedder,
    CachedEmbedder,
    FakeEmbedder,
    GeminiEmbedder,
)


def test_fake_embedder_dimension_and_normalization() -> None:
    embedder = FakeEmbedder(dimension=32)
    assert embedder.dimension == 32

    vec = embedder.embed_query("def hello_world(): return 42")
    assert len(vec) == 32
    norm = float(np.linalg.norm(vec))
    assert abs(norm - 1.0) < 1e-5


def test_fake_embedder_deterministic_results() -> None:
    embedder = FakeEmbedder(dimension=64)
    v1 = embedder.embed_query("class AuthenticationManager:")
    v2 = embedder.embed_query("class AuthenticationManager:")
    assert v1 == v2


def test_fake_embedder_different_texts_differ() -> None:
    embedder = FakeEmbedder(dimension=64)
    v1 = embedder.embed_query("class AuthenticationManager:")
    v2 = embedder.embed_query("def calculate_fibonacci_number(n):")
    assert v1 != v2


def test_fake_embedder_empty_text_returns_zeros() -> None:
    embedder = FakeEmbedder(dimension=16)
    v_empty = embedder.embed_query("")
    assert v_empty == [0.0] * 16

    v_spaces = embedder.embed_query("   \n\t  ")
    assert v_spaces == [0.0] * 16


def test_fake_embedder_rejects_nonpositive_dimension() -> None:
    with pytest.raises(ValueError, match="dimension must be positive"):
        FakeEmbedder(dimension=0)


def test_cached_embedder_reuses_persisted_embedding(tmp_path: Path) -> None:
    fake = FakeEmbedder(dimension=16)
    mock_embedder = MagicMock(wraps=fake)

    cached = CachedEmbedder(
        embedder=mock_embedder,
        cache_dir=tmp_path,
        provider_name="test",
        model_name="fake-16",
    )

    texts = ["function alpha", "function beta"]
    res1 = cached.embed_texts(texts)
    assert len(res1) == 2
    assert mock_embedder.embed_texts.call_count == 1

    # Second call for the same texts should hit disk cache
    res2 = cached.embed_texts(texts)
    assert res1 == res2
    assert mock_embedder.embed_texts.call_count == 1  # No additional calls


def test_cached_embedder_partial_cache_hit(tmp_path: Path) -> None:
    fake = FakeEmbedder(dimension=16)
    mock_embedder = MagicMock(wraps=fake)

    cached = CachedEmbedder(
        embedder=mock_embedder,
        cache_dir=tmp_path,
        provider_name="test",
        model_name="fake-16",
    )

    cached.embed_texts(["already cached"])
    assert mock_embedder.embed_texts.call_count == 1

    # Request one cached and one new item
    results = cached.embed_texts(["already cached", "freshly introduced"])
    assert len(results) == 2
    # mock_embedder should only receive the missing item
    assert mock_embedder.embed_texts.call_count == 2
    mock_embedder.embed_texts.assert_called_with(["freshly introduced"])

def test_gemini_embedder_retries_on_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    from types import SimpleNamespace
    from unittest.mock import MagicMock

    mock_client = MagicMock()

    class FakeRateLimitError(Exception):
        status_code = 429

    mock_emb_item = SimpleNamespace(values=[0.5, 0.5])
    mock_success_response = SimpleNamespace(embeddings=[mock_emb_item])

    # First attempt raises 429, second attempt succeeds
    mock_client.models.embed_content.side_effect = [
        FakeRateLimitError("429 RESOURCE_EXHAUSTED"),
        mock_success_response,
    ]

    # Patch genai.Client
    import google.genai
    monkeypatch.setattr(google.genai, "Client", lambda api_key: mock_client)
    # Patch time.sleep to avoid waiting in tests
    import time
    monkeypatch.setattr(time, "sleep", lambda s: None)

    embedder = GeminiEmbedder(api_key="fake_key", batch_size=2)
    results = embedder.embed_texts(["hello world"])

    assert len(results) == 1
    assert mock_client.models.embed_content.call_count == 2
