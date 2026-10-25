# WhyCode engineering decisions

## Phase 0

- **Provider interface:** callers use a provider-independent `BaseLLM` contract so provider SDK details remain isolated.
- **Local cache:** JSON files keyed by SHA-256 of canonical request inputs make repeated calls reproducible and reduce unnecessary API requests.
- **Testing strategy:** cache behavior is tested with a fake provider, so unit tests do not require network access, an API key, or quota.
- **Initial provider:** Gemini is the first concrete provider. Model availability and account-specific limits must be verified when running the live smoke test.

## Phase 4: Persistent Vector Retrieval & Hybrid Search

- **Embedded storage over external vector DB:** Rather than introducing complex native C++ or client/server vector databases (e.g. Pinecone, Milvus, Qdrant), we chose Python's built-in `sqlite3` + `numpy`. It is 100% self-contained, runs locally on CPU, requires zero background daemons, and stores binary float32 embeddings efficiently as BLOBs.
- **Change-aware incremental synchronization:** Rather than re-chunking and re-embedding all repository files on every query, `IndexSynchronizer` stores SHA-256 file content hashes. Unchanged files are skipped entirely, eliminating redundant computation and embedding API expenses.
- **Reciprocal Rank Fusion (RRF) for Hybrid search:** Combining lexical BM25-style scores (unbounded scale) and cosine similarities (bounded [0, 1]) via linear normalization is notoriously brittle. RRF operates purely on ranked positions ($1 / (k + \text{rank})$), ensuring robust, outlier-resistant rank fusion.
- **Offline testing via FakeEmbedder:** Deterministic pseudo-embeddings derived from character n-grams and token hash buckets allow the entire test suite and evaluation runner to execute offline in seconds with $0 API cost and zero network dependency.
- **Intelligent rate-limit handling with retry delay extraction:** Free-tier embedding models enforce strict token-per-minute (TPM) limits. `GeminiEmbedder` uses smaller batches (8 chunks) and automatically inspects Google's 429 response message for requested retry delays, preventing premature failures.
