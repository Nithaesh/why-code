"""Caching decorator that keeps provider-specific behavior out of callers."""

import logging
from typing import Any

from whycode.llm.base import BaseLLM, LLMResult
from whycode.llm.cache import DiskCache

logger = logging.getLogger(__name__)


class CachedLLM(BaseLLM):
    """Wrap any LLM provider with an on-disk response cache."""

    def __init__(self, provider: BaseLLM, cache: DiskCache, provider_name: str, model: str) -> None:
        self.provider = provider
        self.cache = cache
        self.provider_name = provider_name
        self.model = model

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.0,
        response_schema: dict[str, Any] | None = None,
    ) -> LLMResult:
        """Return cached data when possible; otherwise call and cache the provider."""
        key = self.cache.make_key(
            provider=self.provider_name,
            model=self.model,
            prompt=prompt,
            system=system,
            temperature=temperature,
            response_schema=response_schema,
        )
        cached = self.cache.get(key)
        if cached is not None:
            logger.info("LLM cache hit for model %s", self.model)
            return cached

        logger.info("LLM cache miss for model %s", self.model)
        result = self.provider.generate(
            prompt=prompt,
            system=system,
            temperature=temperature,
            response_schema=response_schema,
        )
        self.cache.set(key, result)
        return result
