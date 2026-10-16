# WhyCode engineering decisions

## Phase 0

- **Provider interface:** callers use a provider-independent `BaseLLM` contract so provider SDK details remain isolated.
- **Local cache:** JSON files keyed by SHA-256 of canonical request inputs make repeated calls reproducible and reduce unnecessary API requests.
- **Testing strategy:** cache behavior is tested with a fake provider, so unit tests do not require network access, an API key, or quota.
- **Initial provider:** Gemini is the first concrete provider. Model availability and account-specific limits must be verified when running the live smoke test.
