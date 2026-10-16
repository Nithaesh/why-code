"""Provider-independent LLM contract used by the rest of WhyCode."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LLMResult:
    """Text and useful metadata returned by an LLM request."""

    text: str
    prompt_tokens: int | None = None
    response_tokens: int | None = None
    latency_seconds: float = 0.0
    cache_hit: bool = False


class BaseLLM(ABC):
    """Common interface so WhyCode does not depend on one provider's SDK."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.0,
        response_schema: dict[str, Any] | None = None,
    ) -> LLMResult:
        """Generate a response using the requested prompt and parameters."""
        raise NotImplementedError
