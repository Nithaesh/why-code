
from pathlib import Path
from typing import Any

import pytest

from whycode.llm.base import BaseLLM, LLMResult
from whycode.retrieval.qa import QuestionAnsweringService


class FakeLLM(BaseLLM):
    """A predictable LLM substitute for tests."""

    def __init__(self, response: str = "Test answer.") -> None:
        self.response = response
        self.last_prompt: str | None = None
        self.last_system: str | None = None
        self.last_temperature: float | None = None
        self.call_count = 0

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.0,
        response_schema: dict[str, Any] | None = None,
    ) -> LLMResult:
        self.call_count += 1
        self.last_prompt = prompt
        self.last_system = system
        self.last_temperature = temperature
        return LLMResult(text=self.response)


def test_ask_returns_answer_and_source_references(
    tmp_path: Path,
) -> None:
    (tmp_path / "cache.py").write_text(
        "def build_cache_key():\n"
        "    cache_key = 'example'\n"
        "    return cache_key\n",
        encoding="utf-8",
    )

    llm = FakeLLM("The function builds a cache key.")
    service = QuestionAnsweringService(tmp_path, llm)

    result = service.ask("How does the cache key work?")

    assert result.question == "How does the cache key work?"
    assert result.answer == "The function builds a cache key."
    assert len(result.sources) == 1
    assert result.sources[0].file_path == "cache.py"
    assert result.sources[0].start_line == 1
    assert result.sources[0].end_line == 3
    assert result.sources[0].chunk_id
    assert llm.call_count == 1


def test_ask_sends_question_and_evidence_to_llm(
    tmp_path: Path,
) -> None:
    (tmp_path / "cache.py").write_text(
        "def build_cache_key():\n"
        "    return 'example'\n",
        encoding="utf-8",
    )

    llm = FakeLLM()
    service = QuestionAnsweringService(tmp_path, llm)

    service.ask("How does the cache key work?")

    assert llm.last_prompt is not None
    assert "How does the cache key work?" in llm.last_prompt
    assert "File: cache.py" in llm.last_prompt
    assert "def build_cache_key():" in llm.last_prompt
    assert llm.last_system is not None
    assert "untrusted data" in llm.last_system
    assert llm.last_temperature == 0.0


def test_ask_returns_fallback_when_no_code_matches(
    tmp_path: Path,
) -> None:
    (tmp_path / "page.py").write_text(
        "def render_page():\n"
        "    return 'hello'\n",
        encoding="utf-8",
    )

    llm = FakeLLM()
    service = QuestionAnsweringService(tmp_path, llm)

    result = service.ask("quantum banana spaceship")

    assert result.sources == ()
    assert "couldn't find relevant code evidence" in result.answer
    assert llm.call_count == 0


def test_ask_rejects_blank_question(tmp_path: Path) -> None:
    service = QuestionAnsweringService(tmp_path, FakeLLM())

    with pytest.raises(ValueError, match="Question cannot be empty"):
        service.ask("   ")


def test_ask_rejects_invalid_top_k(tmp_path: Path) -> None:
    service = QuestionAnsweringService(tmp_path, FakeLLM())

    with pytest.raises(ValueError, match="top_k must be at least 1"):
        service.ask("How does caching work?", top_k=0)
def test_ask_uses_updated_repository_evidence(
    tmp_path: Path,
) -> None:
    source_file = tmp_path / "cache.py"
    source_file.write_text(
        "def get_cache():\n"
        "    return 'JSON cache'\n",
        encoding="utf-8",
    )

    llm = FakeLLM()
    service = QuestionAnsweringService(tmp_path, llm)

    service.ask("How does get_cache work?")
    first_prompt = llm.last_prompt

    source_file.write_text(
        "def get_cache():\n"
        "    return 'Redis cache'\n",
        encoding="utf-8",
    )

    service.ask("How does get_cache work?")
    second_prompt = llm.last_prompt

    assert first_prompt is not None
    assert second_prompt is not None
    assert first_prompt != second_prompt
    assert "JSON cache" in first_prompt
    assert "Redis cache" in second_prompt
    assert llm.call_count == 2