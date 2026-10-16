"""Gemini provider implementation using Google's official Gen AI SDK."""

import logging
import time
from typing import Any

from google import genai
from google.genai import types

from whycode.llm.base import BaseLLM, LLMResult

logger = logging.getLogger(__name__)


def _is_rate_limit_error(error: Exception) -> bool:
    """Recognize common HTTP 429 representations without assuming one SDK type."""
    status = getattr(error, "status_code", None)
    if status is None:
        status = getattr(error, "code", None)
    if status == 429 or str(status) == "429":
        return True
    return "429" in str(error) and any(word in str(error).lower() for word in ("rate", "quota", "resource exhausted"))


class GeminiProvider(BaseLLM):
    """Send prompts to Gemini and normalize the response to LLMResult."""

    def __init__(self, api_key: str, model: str) -> None:
        self.model = model
        self.client = genai.Client(api_key=api_key)

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.0,
        response_schema: dict[str, Any] | None = None,
    ) -> LLMResult:
        """Generate text; retry rate limits up to three times with backoff."""
        config_kwargs: dict[str, Any] = {"temperature": temperature}
        if system:
            config_kwargs["system_instruction"] = system
        if response_schema:
            config_kwargs["response_mime_type"] = "application/json"
            config_kwargs["response_schema"] = response_schema
        config = types.GenerateContentConfig(**config_kwargs)

        started = time.perf_counter()
        for attempt in range(4):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=config,
                )
                usage = getattr(response, "usage_metadata", None)
                prompt_tokens = getattr(usage, "prompt_token_count", None) if usage else None
                response_tokens = getattr(usage, "candidates_token_count", None) if usage else None
                response_text = response.text
                if response_text is None:
                    raise RuntimeError("Gemini returned no text. Check safety feedback or response details.")
                return LLMResult(
                    text=response_text,
                    prompt_tokens=prompt_tokens,
                    response_tokens=response_tokens,
                    latency_seconds=time.perf_counter() - started,
                )
            except Exception as exc:
                if _is_rate_limit_error(exc) and attempt < 3:
                    delay = 2 ** attempt
                    logger.warning("Gemini rate limit (HTTP 429); retrying in %s second(s).", delay)
                    time.sleep(delay)
                    continue
                if _is_rate_limit_error(exc):
                    raise RuntimeError(
                        "Gemini rate limit persisted after 3 retries. Check your quota and try again later."
                    ) from exc
                raise RuntimeError(f"Gemini request failed: {exc}") from exc
        raise RuntimeError("Gemini request failed after retries.")
