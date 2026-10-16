# Phase 0 architecture

`hello.py` -> `CachedLLM` -> `BaseLLM` implementation (`GeminiProvider`)

`CachedLLM` calculates a cache key from provider/model/request parameters. It returns a stored `LLMResult` on a hit; otherwise it calls the provider and stores the result. The Gemini SDK is isolated in `gemini.py`.
