
import pytest

from whycode.ingest.chunker import CodeChunker
from whycode.retrieval.lexical import (
    LexicalRetriever,
    RetrievalResult,
)


@pytest.fixture
def chunks():
    chunker = CodeChunker()

    return (
        chunker.chunk_text(
            "src/config.py",
            "def require_gemini_key():\n"
            "    # Validate the Gemini API key\n"
            "    return True\n",
        )
        + chunker.chunk_text(
            "src/cache.py",
            "class DiskCache:\n"
            "    def save(self, value):\n"
            "        return value\n",
        )
        + chunker.chunk_text(
            "src/git_reader.py",
            "class GitCommitReader:\n"
            "    def read_commit(self, commit_ref):\n"
            "        return commit_ref\n",
        )
    )


def test_retrieves_matching_chunk(chunks):
    retriever = LexicalRetriever()

    results = retriever.search("Gemini API key validation", chunks)

    assert results
    assert results[0].chunk.file_path == "src/config.py"



def test_ranks_more_matches_higher():
    chunker = CodeChunker()
    chunks = [
        chunker.chunk_text(
            "a.py",
            "def cache_value(): pass",
        )[0],
        chunker.chunk_text(
            "b.py",
            "def cache_value():\n"
            "    # cache value\n"
            "    return cache_value\n",
        )[0],
    ]

    results = LexicalRetriever().search("cache_value cache", chunks)

    assert len(results) == 2
    assert results[0].chunk.file_path == "b.py"
    assert results[0].score > results[1].score


def test_empty_query_returns_no_results(chunks):
    assert LexicalRetriever().search("", chunks) == []
    assert LexicalRetriever().search("   ", chunks) == []


def test_no_matching_terms_returns_no_results(chunks):
    results = LexicalRetriever().search(
        "spaceship galaxy telescope",
        chunks,
    )

    assert results == []


def test_top_k_limits_results(chunks):
    results = LexicalRetriever().search(
        "class return",
        chunks,
        top_k=1,
    )

    assert len(results) <= 1


def test_invalid_top_k_raises(chunks):
    with pytest.raises(ValueError, match="top_k"):
        LexicalRetriever().search("Gemini", chunks, top_k=0)


def test_tokenization_is_case_insensitive():
    tokens = LexicalRetriever._tokenize("Gemini API_KEY Validation")

    assert tokens == ["gemini", "api_key", "validation"]


def test_result_requires_positive_score(chunks):
    with pytest.raises(ValueError, match="positive"):
        RetrievalResult(chunk=chunks[0], score=0.0)


def test_ties_are_deterministic():
    chunker = CodeChunker()
    chunks = [
        chunker.chunk_text("z.py", "def hello(): pass")[0],
        chunker.chunk_text("a.py", "def hello(): pass")[0],
    ]

    results = LexicalRetriever().search("hello", chunks)

    assert [r.chunk.file_path for r in results] == ["a.py", "z.py"]


def test_tokenization_splits_underscored_identifiers() -> None:
    tokens = LexicalRetriever._expand_identifiers(
        LexicalRetriever._tokenize("cache_key")
    )

    assert tokens == ["cache_key", "cache", "key"]
