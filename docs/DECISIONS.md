# WhyCode engineering decisions

## Phase 0: Foundation & LLM Abstraction

- **Provider interface:** Callers use a provider-independent `BaseLLM` contract so provider SDK details remain isolated.
- **Local cache:** JSON files keyed by SHA-256 of canonical request inputs make repeated calls reproducible and reduce unnecessary API requests.
- **Testing strategy:** Cache behavior is tested with a fake provider, so unit tests do not require network access, an API key, or quota.
- **Initial provider:** Gemini is the first concrete provider. Model availability and account-specific limits must be verified when running the live smoke test.

---

## Phase 4: Persistent Vector Retrieval & Hybrid Search

- **Embedded storage over external vector DB:** Rather than introducing complex native C++ or client/server vector databases (e.g. Pinecone, Milvus, Qdrant), we chose Python's built-in `sqlite3` + `numpy`. It is 100% self-contained, runs locally on CPU, requires zero background daemons, and stores binary float32 embeddings efficiently as BLOBs.
- **Change-aware incremental synchronization:** Rather than re-chunking and re-embedding all repository files on every query, `IndexSynchronizer` stores SHA-256 file content hashes. Unchanged files are skipped entirely, eliminating redundant computation and embedding API expenses.
- **Reciprocal Rank Fusion (RRF) for Hybrid search:** Combining lexical BM25-style scores (unbounded scale) and cosine similarities (bounded [0, 1]) via linear normalization is notoriously brittle. RRF operates purely on ranked positions ($1 / (k + \text{rank})$), ensuring robust, outlier-resistant rank fusion.
- **Offline testing via FakeEmbedder:** Deterministic pseudo-embeddings derived from character n-grams and token hash buckets allow the entire test suite and evaluation runner to execute offline in seconds with $0 API cost and zero network dependency.
- **Intelligent rate-limit handling with retry delay extraction:** Free-tier embedding models enforce strict token-per-minute (TPM) limits. `GeminiEmbedder` uses smaller batches (8 chunks) and automatically inspects Google's 429 response message for requested retry delays, preventing premature failures.

---

## Phase 5: Grounded Hybrid RAG Pipeline & Multi-Source Synthesis

- **Context distillation over raw chunk concatenations:** Retrieved chunks often overlap by 10-20 lines or come from adjacent spans in the same file. Feeding raw chunks to an LLM wastes context tokens and degrades attention. `ContextDistiller` coalesces overlapping line ranges into contiguous file spans and enforces a hard character ceiling.
- **Post-generation citation verification:** LLMs frequently produce plausible-sounding citations that refer to files or line numbers not actually present in the context. `CitationVerifier` programmatically extracts citations and verifies file and line-range containment against the retrieved evidence, computing a quantitative grounding confidence score.
- **Untrusted data boundary:** Prompts explicitly inform the model that repository code, comments, and strings are untrusted data to be analyzed, not instructions to be executed.
- **Framework simplicity vs LangChain:** For linear pipelines (Retrieve -> Distill -> Generate -> Verify), direct Python services provide complete transparency, faster execution, zero dependency churn, and superior testability.

---

## Phase 6: Repository Structure & Git-History Association

- **Standard Library `ast` over Heavy Static Analysis Tools:** Python's standard `ast` module is fast, robust, and requires zero external dependencies. It extracts class hierarchies, function definitions, parameters, docstrings, imports, and function calls safely without executing code.
- **Diff Hunk Line Span Intersect for Git Churn:** Instead of brittle line-blaming or slow git-log-L subprocess commands that break across line moves, `SymbolChurnTracker` checks whether unified diff hunks (`@@ -old_start,old_count +new_start,new_count @@`) intersect the symbol's start and end lines. This correlates AST symbols to Git commits accurately and fast.
- **Callable Symbol Filtering for Callers:** When mapping function calls, classes can contain methods that invoke functions. However, attributing caller relationships to the enclosing class creates misleading edges. `CodebaseGraph.get_callers` explicitly restricts callers to callable symbols (`function` and `method`).

---

## Phase 7: Stateful Agentic Investigation Workflows

- **Explicit State-Machine Orchestrator vs Opaque Agent Frameworks:** Rather than adopting heavy, black-box agent frameworks with volatile prompt engineering, WhyCode uses an explicit state machine (`InvestigationState` and `InvestigationAgent`). State transitions (Plan -> Execute Tools -> Evaluate Sufficiency -> Synthesize) are fully deterministic, auditable, and easily debugged.
- **Strict Iteration Ceiling Guardrail:** Autonomous multi-step loops risk infinite cycles. An explicit iteration budget (`max_iterations`, default 3) guarantees termination. When the budget is exhausted, the evaluator forces sufficiency and proceeds to synthesis with honest acknowledgment of remaining gaps.
- **Cross-Modal Hop Discovery:** During AST symbol inspection, Git commit revisions touching modified symbols are automatically queued for unified diff inspection within the same hop, bridging code structure and temporal history seamlessly.

---

## Phase 8: Developer Interfaces & REST API

- **FastAPI Application Factory with Dependency Injection:** `create_app` accepts optional `llm` and `embedder` overrides stored in `app.state.services`. This allows unit tests to inject `FakeLLM` and `FakeEmbedder` seamlessly without needing live environment keys.
- **Typed Pydantic v2 Contracts:** Standardized schemas with field bounds prevent invalid payloads from reaching internal services and auto-generate OpenAPI documentation.
- **Unified CLI `serve` Command:** Developers can spin up the REST server locally with `whycode serve` for IDE extensions and external tools.

---

## Phase 9: System Evaluation & Security Audit

- **Automated Metric Suite:** Evaluation benchmarks compute Hit@K and MRR across Lexical, Vector, and Hybrid modes, evaluate citation verification precision, and verify agent convergence.
- **Adversarial Hardening:** Formalized verification confirms that code containing prompt injection instructions (`SYSTEM OVERRIDE`) is isolated as untrusted data and cannot hijack LLM generation or bypass citation verification.
- **Subprocess Security:** Subprocess executions pass explicit argument sequences, preventing shell argument injection or arbitrary command execution.
