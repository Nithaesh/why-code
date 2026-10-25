"""Tests for caching behavior; these tests never contact Gemini."""

from pathlib import Path

from whycode.llm.base import BaseLLM, LLMResult
from whycode.llm.cache import DiskCache
from whycode.llm.client import CachedLLM


class FakeLLM(BaseLLM):
    """Predictable provider used to test the cache without network access."""

    def __init__(self) -> None:
        self.calls = 0

    def generate(self, prompt, system=None, temperature=0.0, response_schema=None):
        self.calls += 1
        return LLMResult(text=f"fake answer {self.calls}", prompt_tokens=3, response_tokens=4, latency_seconds=0.1)


def test_second_identical_request_is_a_cache_hit(tmp_path: Path) -> None:
    provider = FakeLLM()
    llm = CachedLLM(provider, DiskCache(tmp_path), "fake", "fake-model")

    first = llm.generate("same prompt", temperature=0.0)
    second = llm.generate("same prompt", temperature=0.0)

    assert first.text == "fake answer 1"
    assert first.cache_hit is False
    assert second.text == "fake answer 1"
    assert second.cache_hit is True
    assert provider.calls == 1


def test_different_prompts_do_not_share_cache_entries(tmp_path: Path) -> None:
    provider = FakeLLM()
    llm = CachedLLM(provider, DiskCache(tmp_path), "fake", "fake-model")

    first = llm.generate("prompt one")
    second = llm.generate("prompt two")

    assert first.text == "fake answer 1"
    assert second.text == "fake answer 2"
    assert provider.calls == 2


def test_cache_key_changes_when_generation_parameters_change() -> None:
    first = DiskCache.make_key("gemini", "model", "prompt", None, 0.0, None)
    second = DiskCache.make_key("gemini", "model", "prompt", None, 0.7, None)
    assert first != second


def test_cached_llm_accepts_system_instruction_alias(tmp_path: Path) -> None:
    provider = FakeLLM()
    llm = CachedLLM(provider, DiskCache(tmp_path), "fake", "fake-model")

    res = llm.generate("test prompt", system_instruction="System prompt via alias")
    assert res.text == "fake answer 1"

