# WhyCode

WhyCode investigates Git history and repository source code to answer why and how code changed, with evidence-backed commit and source citations.

Designed as an educational and production-grade GenAI engineering platform for deep software archaeology.

---

## Capabilities Overview (Phases 0–9)

1. **LLM Abstraction & Response Caching (Phase 0):**
   - Provider-independent `BaseLLM` interface returning typed `LLMResult`.
   - Google Gemini provider integration (`google-genai`) with automatic exponential backoff rate-limit handling.
   - Deterministic disk-based JSON response caching keyed by SHA-256 of canonical generation parameters.

2. **Git Commit Extraction & Summarization (Phase 1):**
   - Direct Git inspection via command-line subprocesses (`git show`, `git diff-tree -z --no-renames`, `git log`).
   - Structured commit summarization validating evidence against actual diffs and flagging uncertainty.
   - CLI commands: `history`, `show`, `summarize`.

3. **Repository Intelligence & Chunking (Phase 2):**
   - Deterministic repository scanning with file size limits, binary detection, and sensitive file exclusion.
   - Traceable source code chunking with overlapping line windows and stable content hashes.
   - Fast lexical search with BM25-style keyword scoring, regex-based definition boosting, and CamelCase/snake_case tokenization.
   - CLI command: `search`.

4. **Codebase RAG & Question Answering (Phase 3):**
   - Structured evidence context building with file paths and line ranges.
   - Source-grounded Q&A service defending against prompt injection by isolating untrusted repository text.
   - CLI command: `ask`.

5. **Persistent Vector Retrieval & Hybrid Search (Phase 4):**
   - Dense vector embeddings via `BaseEmbedder`, `GeminiEmbedder` (`gemini-embedding-001`), `CachedEmbedder`, and offline `FakeEmbedder`.
   - Lightweight, embedded vector store using Python's standard `sqlite3` + `numpy` for chunk metadata and cosine similarity.
   - Change-aware synchronization (`IndexSynchronizer`): tracks SHA-256 content hashes, only re-indexing modified/added files and pruning deleted ones.
   - Hybrid retrieval fusing Lexical and Dense Vector search via Reciprocal Rank Fusion (RRF).

6. **Grounded Hybrid RAG & Citation Verification (Phase 5):**
   - Connects persistent hybrid retrieval directly to the question-answering pipeline.
   - Context distillation (`ContextDistiller`): merges overlapping/adjacent chunks into unified line spans and enforces context character budgets.
   - Post-generation citation verification (`CitationVerifier`): parses LLM citations (`[Source N]`, `file.py:lines`), validates them against retrieved source blocks, flags hallucinations, and computes a grounding confidence score.

7. **Repository Structure & Git-History Association (Phase 6):**
   - AST-based symbol parsing (`ASTSymbolParser`) extracting Python classes, functions, methods, parameters, and calls using standard library `ast`.
   - Code dependency graph (`CodebaseGraph`) indexing definitions, callers, callees, and module-level imports.
   - Symbol Git churn tracking (`SymbolChurnTracker`) correlating code symbols to the exact Git commits that modified their line spans.
   - CLI commands: `symbol` and `churn`.

8. **Stateful Agentic Investigation Workflows (Phase 7):**
   - Multi-hop diagnostic investigation agent (`InvestigationAgent`) that formulates hypotheses, executes tools across AST graphs, vector search, and Git commit diffs, reflects on evidence sufficiency, and synthesizes grounded diagnostic reports.
   - Bounded execution guardrails (`max_iterations` cap) preventing runaway loops or token costs.
   - CLI command: `investigate`.

9. **Developer REST API & Interactive Server (Phase 8):**
   - Asynchronous FastAPI application (`whycode.api`) exposing all capabilities over typed REST endpoints (`/health`, `/search`, `/ask`, `/symbol`, `/churn`, `/investigate`).
   - OpenAPI Swagger documentation available at `/docs` and `/redoc`.
   - CLI command: `serve`.

10. **System Evaluation & Security Audit Hardening (Phase 9):**
    - End-to-end evaluation harness (`eval/eval_system.py`) measuring Hit@K, MRR, citation verification precision, and agent multi-hop convergence.
    - Security audit test suite (`tests/test_security_audit.py`) validating prompt injection isolation, subprocess argument escaping, and API boundary protections.

---

## Architecture Flow

```
                      ┌────────────────────────────────────────┐
                      │          User Query / REST API         │
                      └───────────────────┬────────────────────┘
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
       [Single-Turn RAG: `ask`]                     [Multi-Hop Agent: `investigate`]
                  │                                               │
                  │                                  ┌────────────┴────────────┐
                  │                                  ▼                         ▼
                  │                           Plan & Hypothesize         Reflect & Evaluate
                  │                                  │                         ▲
                  ├──────────────────────────────────┼─────────────────────────┤
                  ▼                                  ▼                         │
          [Hybrid Retriever]                 [Codebase AST Graph]       [Git Commit Reader]
          - BM25 Lexical                     - Callers & Callees        - Unified Diffs
          - SQLite Dense Vector              - Definitions              - Commit History
          - Reciprocal Rank Fusion           - Symbol Churn             - Churn Hotspots
                  │                                  │                         │
                  └──────────────────────────────────┼─────────────────────────┘
                                                     ▼
                                            [Context Distillation]
                                            - Chunk merging & budget
                                                     ▼
                                            [LLM Generation]
                                            - GeminiProvider / CachedLLM
                                                     ▼
                                          [Citation Verification]
                                          - Hallucination detection
                                          - Grounding confidence score
                                                     ▼
                                            [Grounded Report / JSON]
```

---

## Setup & Installation

```powershell
# 1. Clone repository and navigate to root
cd D:\Nithaesh\Programming\whycode

# 2. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt
pip install -e .

# 4. Optional: Configure Gemini API Key for live LLM / embeddings
Copy-Item .env.example .env
# Edit .env and supply GEMINI_API_KEY if making live API calls
```

---

## Running the Automated Test Suite

All tests run **100% offline** with zero external network access, API keys, or quota charges using `FakeLLM` and `FakeEmbedder`:

```powershell
python -m pytest -v
```

---

## Running System Evaluations

Execute the automated benchmark across retrieval accuracy (MRR, Hit@K), citation verification fidelity, and agentic multi-hop resolution:

```powershell
python eval\eval_system.py
```

Results are saved to `eval/results/system_benchmark.json`.

---

## CLI Reference

### 1. Agentic Multi-Hop Investigation (Phase 7)
```powershell
whycode investigate . -q "Why did token validation change and what callers were affected?" --max-steps 3
```

### 2. REST API Server (Phase 8)
```powershell
whycode serve . --host 127.0.0.1 --port 8000
# Open http://127.0.0.1:8000/docs for Swagger UI
```

### 3. Codebase Q&A with Citation Verification (Phase 3 & 5)
```powershell
whycode ask . --question "How does DiskCache construct cache keys?" --mode hybrid
```

### 4. Code Search (Phase 2 & 4)
```powershell
whycode search . --query "make_key" --mode hybrid --top-k 5
```

### 5. AST Symbol Inspection & Call Graph (Phase 6)
```powershell
whycode symbol . --name DiskCache
```

### 6. Git Churn Hotspots (Phase 6)
```powershell
whycode churn . --limit 10
```

### 7. Commit Summarization & History (Phase 1)
```powershell
whycode history . --limit 5
whycode show . --commit HEAD
whycode summarize . --commit HEAD
```
