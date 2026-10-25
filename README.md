# WhyCode ⚡

> **Universal Codebase Intelligence & Software Archaeology Platform**  
> Ask questions and investigate **any GitHub repository** with compiler AST dependency graphs, Git revision blame, hybrid RRF search, and deterministic citation verification.

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg?logo=react)](https://react.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-v4-38B2AC.svg?logo=tailwind-css)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests: 171 Passed](https://img.shields.io/badge/Tests-171%20Passed-brightgreen.svg)]()
[![Offline Test Cost](https://img.shields.io/badge/Test%20Cost-%240.00-success.svg)]()

---

## 🌟 The Core Innovation

Most AI code tools suffer from **two fatal flaws**:
1. **Amnesia (Ignoring History):** They only see current files. They cannot tell you *why* an architectural decision was made 6 months ago, which commits caused it, or who authored the changes.
2. **Hallucination:** They invent phantom files, hallucinate line numbers, and guess how functions work.

**WhyCode** fixes this with a **Deterministic Software Archaeology Pipeline**:
- 🌐 **Universal GitHub Intelligence:** Point to **any public GitHub repository** (`pallets/flask`, `psf/requests`, `tiangolo/fastapi`) or your local directory. It shallow-clones and indexes in seconds.
- 🌳 **Compiler AST Trees:** Deeply parses Python ASTs (`ast.NodeVisitor`) to extract classes, functions, parameters, and upstream/downstream call graphs.
- 📜 **Git Revision Blame:** Correlates AST symbol line spans with Git commits to pinpoint **modification velocity** and technical debt hotspots.
- 🔍 **Hybrid Search (RRF):** Merges BM25 lexical keyword matching with Google Gemini dense vector embeddings via **Reciprocal Rank Fusion ($k=60$)**.
- 🛡️ **Zero Hallucination Tolerance:** Every statement is audited by a post-generation **Citation Verifier** that verifies on-disk files and line spans, assigning an audited grounding confidence score.
- 🤖 **Autonomous Multi-Hop ReAct Agent:** Deconstructs complex questions into hypotheses, navigates AST dependencies across multiple hops, and synthesizes structured architectural reports.
- 🎨 **Apple/Awwwards-Grade Web App:** React 19 + TypeScript + Tailwind v4 interactive workbench with zero CORS issues, served directly by FastAPI.

---

## 🏗️ System Architecture

```
                                  USER INTERFACE
          ┌─────────────────────────────────────────────────────────────┐
          │  React 19 + Tailwind v4 Web Studio (http://127.0.0.1:8080)   │
          │         CLI Terminal (`whycode`)  •  REST API (`/docs`)     │
          └──────────────────────────────┬──────────────────────────────┘
                                         │
                                         ▼
                             FASTAPI UNIFIED SERVER
          ┌─────────────────────────────────────────────────────────────┐
          │  - Dynamic GitHub Cloner & Repo Hot-Swapper                 │
          │  - Asynchronous Pre-Warmed Services (`app.state.services`)   │
          │  - Single-Port Static SPA Mount (`web/`)                    │
          └──────────────────────────────┬──────────────────────────────┘
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
      [Single-Turn Grounded RAG]                     [Multi-Hop ReAct Agent]
                 │                                               │
                 │                                  ┌────────────┴────────────┐
                 │                                  ▼                         ▼
                 │                           Plan & Hypothesize         Reflect & Evaluate
                 │                                  │                         ▲
                 ├──────────────────────────────────┼─────────────────────────┤
                 ▼                                  ▼                         │
         [Hybrid Retriever]                 [Codebase AST Graph]       [Git Commit Engine]
         - BM25Okapi Lexical                - Callers & Callees        - Unified Diffs
         - SQLite Dense Vectors             - Definitions & Params     - Commit History
         - Reciprocal Rank Fusion           - Symbol Churn Velocity    - Hotspot Ranking
                 │                                  │                         │
                 └──────────────────────────────────┼─────────────────────────┘
                                                    ▼
                                           [Context Distiller]
                                           - Adjacent chunk merging
                                           - Token character budget
                                                    ▼
                                           [Deterministic Cache]
                                           - SHA-256 parameter hashing
                                           - $0.00 offline test cost
                                                    ▼
                                          [Gemini LLM Generation]
                                           - gemini-3.5-flash-lite
                                                    ▼
                                         [Citation Verification]
                                         - Line-by-line disk audit
                                         - Grounding confidence score
                                                    ▼
                                          [Verified Report / JSON]
```

---

## 🚀 Quickstart

### 1. Prerequisites
- **Python 3.11+**
- **Node.js 18+** (for frontend development/builds)
- **Git**

### 2. Installation
```powershell
# 1. Clone repository
git clone https://github.com/Nithaesh/why-code.git
cd why-code

# 2. Set up virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install Python dependencies in editable mode
pip install -e .

# 4. Supply Gemini API Key (optional for offline tests, required for live LLM generation)
Copy-Item .env.example .env
# Edit .env and set GEMINI_API_KEY="your-api-key"
```

### 3. Launch Full-Stack Web Studio
```powershell
python -m whycode serve . --host 127.0.0.1 --port 8080
```
Open **[http://127.0.0.1:8080](http://127.0.0.1:8080)** in your browser!
- **Interactive REST API Docs (Swagger):** [http://127.0.0.1:8080/docs](http://127.0.0.1:8080/docs)
- **ReDoc API Spec:** [http://127.0.0.1:8080/redoc](http://127.0.0.1:8080/redoc)

---

## 💻 CLI Commands Reference

WhyCode can be operated completely from the command line:

### 1. Multi-Hop Software Archaeology Agent
```powershell
# Run autonomous investigation across AST, Git commits, and code search
python -m whycode investigate "Why was SQLite chosen for vector indexing?" --steps 3
```

### 2. Grounded Q&A with Citation Audit
```powershell
# Ask questions with line-level verified citations
python -m whycode ask "How does ContextDistiller enforce character budgets?" --mode hybrid
```

### 3. AST Symbol & Caller Graph
```powershell
# Inspect function/class definitions, upstream callers, and downstream callees
python -m whycode symbol ASTSymbolParser
```

### 4. Git Churn Hotspots
```powershell
# Pinpoint the most frequently modified symbols and technical debt hotspots
python -m whycode churn --limit 10
```

### 5. Hybrid Code Search (RRF)
```powershell
# Search code using Reciprocal Rank Fusion blending BM25 and vector embeddings
python -m whycode search "Reciprocal rank fusion" --mode hybrid --top-k 5
```

### 6. Git Commit Archaeology
```powershell
# View recent commits and parse unified diffs
python -m whycode history -n 5
python -m whycode show HEAD
```

---

## 🧪 Testing & Verification

WhyCode is built with rigorous test coverage. All **171 automated tests** run **100% offline** with $0.00 API cost using deterministic local mocks and SQLite disk caching:

```powershell
# Run the complete test suite (171 tests)
pytest -v

# Run API and Web Server tests
pytest -v tests/test_api.py

# Run Multi-Hop Agent tests
pytest -v tests/test_agent_orchestrator.py

# Run Citation Verification tests
pytest -v tests/test_citation_verifier.py

# Run Information Retrieval Benchmarks (MRR & Hit@K)
pytest -v tests/test_retrieval_evaluation.py

# Run Security Audit (Path traversal, command injection)
pytest -v tests/test_security_audit.py
```

---

## 📚 Educational Phase Curriculum

WhyCode is documented as a step-by-step master curriculum for Computer Science students learning GenAI engineering from first principles.

| Phase | Topic | Theory & Concepts | Report |
|---|---|---|---|
| **Phase 00** | **Foundations & Caching** | Python packaging, Strategy Pattern for LLMs, SHA-256 disk caching, HTTP 429 rate limit backoff. | [Read Report](docs/phases/PHASE_00_FOUNDATION.md) |
| **Phase 01** | **Git Archaeology** | Git DAG traversal, Unified Diffs parsing (`@@ -start,len +start,len @@`), commit blame. | [Read Report](docs/phases/PHASE_01_GIT_ARCHAEOLOGY.md) |
| **Phase 02** | **AST Compiler Trees** | Why regex fails on code, Python `ast.NodeVisitor`, class/function/async AST parsing, caller/callee trees. | [Read Report](docs/phases/PHASE_02_AST_CODE_INTELLIGENCE.md) |
| **Phase 03** | **Why RAG? Chunking & BM25** | Attention dilution in large context windows, sliding-window chunking, inverted index, BM25Okapi math. | [Read Report](docs/phases/PHASE_03_CODEBASE_CHUNK_AND_LEXICAL.md) |
| **Phase 04** | **Vector Embeddings & RRF** | High-dimensional latent space (768-D), Cosine geometry, SQLite vector storage, Reciprocal Rank Fusion ($k=60$). | [Read Report](docs/phases/PHASE_04_VECTOR_EMBEDDINGS_AND_HYBRID_RRF.md) |
| **Phase 05** | **Grounded RAG & Verifier** | Context distillation, LLM hallucination prevention, post-generation line audit, grounding score. | [Read Report](docs/phases/PHASE_05_GROUNDED_RAG_AND_CITATION_VERIFIER.md) |
| **Phase 06** | **Code Graph & Git Churn** | Software churn theory, correlating AST symbol lines with Git diffs, technical debt hotspots. | [Read Report](docs/phases/PHASE_06_CODE_GRAPH_AND_GIT_CHURN.md) |
| **Phase 07** | **Multi-Hop Agent (ReAct)** | Why single-shot RAG fails on deep bugs, ReAct pattern, tool dispatching, sufficiency judge, loop guardrails. | [Read Report](docs/phases/PHASE_07_MULTI_HOP_AGENTIC_WORKFLOWS.md) |
| **Phase 08** | **FastAPI Developer REST API** | REST API architecture, Starlette async `lifespan`, Pydantic v2 validation, single-port SPA mounting. | [Read Report](docs/phases/PHASE_08_DEVELOPER_INTERFACES_FASTAPI.md) |
| **Phase 09** | **Evaluation & Security** | IR metrics (MRR, Hit@K), path traversal prevention, command injection defense, prompt injection guardrails. | [Read Report](docs/phases/PHASE_09_EVALUATION_AND_SECURITY.md) |
| **Phase 10** | **React 19 & GitHub Landing** | Vite + React 19 + Tailwind v4, 11-Element Conversion Landing Page, GitHub repo cloner, 5-tab workbench. | [Read Report](docs/phases/PHASE_10_FULLSTACK_REACT_FRONTEND.md) |

👉 **[Master Curriculum Table of Contents](docs/phases/README.md)**

---

## 🛠️ Frontend Development

The frontend is built with **React 19**, **TypeScript**, and **Tailwind CSS v4**:

```powershell
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start Vite dev server (proxies API to :8080)
npm run dev

# Compile production bundle directly into web/ directory
npm run build
```

---

## 🔒 Security Hardening

- **Path Traversal Protection:** All file paths are resolved and asserted via `path.is_relative_to(repo_root)` to prevent directory escape attacks.
- **Subprocess Argument Safety:** All Git commands run with `shell=False` passing argument arrays, neutralizing command injection attempts.
- **Git URL Whitelisting:** Clone URLs are validated via regex against strict GitHub URL patterns, blocking arbitrary script URLs or malicious flags.
- **Prompt Injection Isolation:** Untrusted repository code chunks are encapsulated strictly as JSON data blocks with immutable instructions.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
