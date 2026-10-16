"""Small live smoke test for the Phase 0 LLM path."""

import logging
import sys

from whycode.config import Settings
from whycode.llm.cache import DiskCache
from whycode.llm.client import CachedLLM
from whycode.llm.gemini import GeminiProvider


def main() -> int:
    """Make one short request and show response/cache metadata."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    settings = Settings()
    try:
        api_key = settings.require_gemini_key()
        if settings.whycode_provider.lower() != "gemini":
            raise ValueError("Phase 0 currently supports WHYCODE_PROVIDER=gemini only.")
        provider = GeminiProvider(api_key=api_key, model=settings.gemini_model)
        llm = CachedLLM(
            provider=provider,
            cache=DiskCache(settings.whycode_cache_dir),
            provider_name="gemini",
            model=settings.gemini_model,
        )
        result = llm.generate(
            prompt="Explain what a Git commit is in exactly two short sentences.",
            system="You are a concise programming tutor.",
            temperature=settings.whycode_temperature,
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("\nWhyCode LLM smoke test")
    print("----------------------")
    print(result.text)
    print(f"\nModel: {settings.gemini_model}")
    print(f"Cache hit: {result.cache_hit}")
    print(f"Request latency (seconds): {result.latency_seconds:.3f}")
    print(f"Prompt tokens: {result.prompt_tokens if result.prompt_tokens is not None else 'not reported'}")
    print(f"Response tokens: {result.response_tokens if result.response_tokens is not None else 'not reported'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
