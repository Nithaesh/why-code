# WhyCode Architecture Overview (Phases 0–9)

WhyCode is organized into modular subsystems with decoupled contracts:

```
whycode/
├── config.py             # Central Pydantic BaseSettings configuration
├── git/                  # Subprocess Git inspection and evidence models
│   ├── history.py        # GitHistoryReader (bounded commit traversal)
│   └── reader.py         # GitCommitReader (null-byte diff extraction)
├── ingest/               # Repository scanning and source code chunking
│   ├── scanner.py        # RepositoryScanner (filtering, size limits)
│   ├── chunker.py        # CodeChunker (sliding line window, chunk_id hashing)
│   └── pipeline.py       # Ingestion orchestration
├── llm/                  # LLM and embedding abstraction layer
│   ├── base.py           # BaseLLM, LLMResult, BaseEmbedder contracts
│   ├── cache.py          # DiskCache (SHA-256 canonical request caching)
│   ├── client.py         # CachedLLM decorator
│   ├── gemini.py         # GeminiProvider (text generation + backoff)
│   └── embedding.py      # BaseEmbedder, GeminiEmbedder, CachedEmbedder, FakeEmbedder
├── retrieval/            # Lexical, Vector, and Hybrid retrieval engines
│   ├── lexical.py        # LexicalRetriever (BM25 + definition boosting)
│   ├── index.py          # VectorIndex (SQLite + NumPy vector storage)
│   ├── sync.py           # IndexSynchronizer (change-aware incremental indexing)
│   ├── vector.py         # VectorRetriever (dense cosine similarity)
│   ├── hybrid.py         # HybridRetriever (Reciprocal Rank Fusion)
│   ├── distiller.py      # ContextDistiller (chunk coalescing and budget pruning)
│   ├── verifier.py       # CitationVerifier (regex citation grounding check)
│   ├── qa.py             # QuestionAnsweringService (grounded code Q&A)
│   └── service.py        # CodebaseSearchService (search coordinator)
├── graph/                # AST code structure and Git churn correlation
│   ├── ast_parser.py     # ASTSymbolParser (class/function/call parsing via ast)
│   ├── dependency.py     # CodebaseGraph (callers, callees, definitions)
│   ├── churn.py          # SymbolChurnTracker (commit hunk intersection)
│   └── service.py        # CodeGraphService (coordination and hotspot ranking)
├── agent/                # Stateful multi-step investigation orchestrator
│   ├── state.py          # EvidenceItem, InvestigationPlan, InvestigationState
│   ├── tools.py          # InvestigationToolbox (unified tool layer)
│   └── orchestrator.py   # InvestigationAgent (planning, reflection, synthesis)
├── api/                  # Developer REST API
│   ├── app.py            # create_app application factory
│   ├── routes.py         # FastAPI routes (/health, /search, /ask, /symbol, /churn, /investigate)
│   └── schemas.py        # Pydantic v2 request/response schemas
├── summarizer/           # Structured commit analysis
│   ├── models.py         # CommitSummary, EvidenceItem Pydantic schemas
│   └── service.py        # CommitSummaryService (hallucination defense)
└── investigation/        # Commit investigation coordination
    └── service.py        # CommitInvestigationService
```

---

## 1. Grounded Hybrid Retrieval (Phases 2, 4, 5)

* **Persistent Vector Storage:** SQLite relational tables (`indexed_files` and `chunks`), storing dense embeddings as raw float32 BLOBs. Cosine similarity is computed directly in NumPy:
  $$\text{sim}(u, v) = \frac{u \cdot v}{\|u\|_2 \|v\|_2}$$
* **Change-Aware Synchronization:** Calculates file content SHA-256 hashes to skip unchanged files during re-indexing, preventing unnecessary embedding API calls.
* **Reciprocal Rank Fusion (RRF):** Fuses lexical BM25 and dense vector rankings:
  $$RRF(d) = \sum_{m \in \{\text{lexical}, \text{vector}\}} \frac{w_m}{60 + \text{rank}_m(d)}$$
* **Context Distillation:** Adjacent and overlapping chunks are merged into unified line ranges, capped by character budgets to prevent prompt bloat.
* **Citation Verification:** Regex parses cited files and line numbers, validating them against the retrieved source blocks and computing a grounding confidence score.

---

## 2. AST Structure & Git Churn Correlation (Phase 6)

* **Abstract Syntax Tree Extraction:** Uses Python's standard `ast` module to extract classes, functions, async functions, docstrings, parameters, and calls.
* **Caller & Callee Inversion:** Indexes which functions invoke a target symbol, enabling ripple-effect impact analysis.
* **Unified Diff Hunk Intersection:** Parses unified diff line ranges (`@@ -old_start,old_count +new_start,new_count @@`) to map commit revisions directly to AST symbol spans.

---

## 3. Stateful Agentic Investigation Workflows (Phase 7)

```
                     ┌────────────────────────────────────────┐
                     │          User Diagnostic Query         │
                     └───────────────────┬────────────────────┘
                                         ▼
                     ┌────────────────────────────────────────┐
                     │      Phase 1: Formulate Roadmap        │
                     │  - Decompose into hypotheses           │
                     │  - Propose target symbols & queries    │
                     └───────────────────┬────────────────────┘
                                         ▼
                     ┌────────────────────────────────────────┐
                     │      Phase 2: Multi-Tool Execution     │
                     │  - Tool 1: AST Symbol & Caller Graph   │
                     │  - Tool 2: Hybrid Code Search          │
                     │  - Tool 3: Git Commit Diff Inspection  │
                     └───────────────────┬────────────────────┘
                                         ▼
                     ┌────────────────────────────────────────┐
                     │      Phase 3: Sufficiency Evaluation   │
                     │  - Judge if evidence answers inquiry   │
                     │  - Guardrail: Hard max-iteration cap   │
                     └──────────┬───────────────────┬─────────┘
        Insufficient &          │                   │ Sufficient OR
        iteration < max_budget  │                   │ budget exhausted
                                ▼                   ▼
             ┌─────────────────────────┐     ┌────────────────────────────────────────┐
             │      Refine Plan        │     │      Phase 4: Evidence Synthesis       │
             │ - Pick next symbol/hop  │     │ - Executive summary & timeline         │
             └─────────────┬───────────┘     │ - Root causes & impacted callers       │
                           │                 │ - Verified citations & uncertainties   │
                           └────────►(Loop)  └───────────────────┬────────────────────┘
                                                                 ▼
                                                    [Final Investigation Report]
```

* **Deterministic State Machine:** Manages state progression through `InvestigationState`, tracking accumulated `evidence`, `visited_symbols`, and `visited_commits`.
* **Bounded Iteration Guardrail:** Strict `max_iterations` limit terminates reasoning loops deterministically, preventing infinite cycling or runaway token spend.

---

## 4. Developer REST API (Phase 8)

* **FastAPI Application Factory:** `create_app` wires dependency injection via `app.state.services`, enabling mock injection for fast offline testing.
* **REST Endpoints:** Exposes `/health`, `/search`, `/ask`, `/symbol/{name}`, `/churn`, and `/investigate`.
* **OpenAPI Documentation:** Interactive documentation at `/docs` (Swagger UI) and `/redoc`.

---

## 5. System Evaluation & Security Audit (Phase 9)

* **System Benchmark Harness:** `eval/eval_system.py` automatically measures retrieval MRR, Hit@K, citation verification fidelity, and agent convergence.
* **Security Hardening:** Enforces untrusted input isolation in LLM prompts, sanitized subprocess arguments, syntax error tolerance, and API boundary validations.
