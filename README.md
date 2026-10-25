# WhyCode

WhyCode investigates Git history and repository source code to answer why and how code changed, with evidence-backed commit and source citations.

## Capabilities (Phases 0–4)

1. **LLM Abstraction & Response Caching (Phase 0):**
   - Provider-independent `BaseLLM` interface returning typed `LLMResult`.
   - Google Gemini provider integration (`google-genai`) with automatic exponential backoff rate-limit handling.
   - Deterministic disk-based JSON response caching keyed by SHA-256 of canonical generation parameters.

2. **Git Commit Extraction & Summarization (Phase 1):**
   - Direct Git inspection via command-line subprocesses (`git show`, `git diff-tree -z --no-renames`, `git log`).
   - Structured commit summarization validating evidence against actual diffs and flagging uncertainty.
   - CLI commands: `history`, `show`, `summarize`.

3. **Repository Intelligence (Phase 2):**
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
   - Automated retrieval evaluation benchmark (`eval/eval_retrieval.py`) measuring Hit@1, Hit@3, Hit@5, and Mean Reciprocal Rank (MRR).

---

## Requirements

- Python 3.11
- Git (on system `PATH`)
- Optional: A Google Gemini API key for live generation and embeddings

---

## Setup (Windows PowerShell)

```powershell
cd D:\Nithaesh\Programming\whycode
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
Copy-Item .env.example .env
```

If running live LLM or embedding calls, edit `.env` and set `GEMINI_API_KEY`. Never commit `.env` to Git.

---

## Running Automated Tests

All tests run completely offline with fake providers and require zero network access, API keys, or quota:

```powershell
python -m pytest -v
```

---

## Running Retrieval Evaluation Benchmark

Evaluate Lexical, Semantic (Vector), and Hybrid retrieval on the curated benchmark dataset:

```powershell
# Fast offline evaluation using deterministic pseudo-embeddings:
python eval\eval_retrieval.py

# Optional: Live evaluation using Gemini embeddings (requires GEMINI_API_KEY in .env):
python eval\eval_retrieval.py --live
```

---

## CLI Usage

### 1. Search Codebase
```powershell
# Lexical search (default):
python -m whycode search . --query "DiskCache"

# Hybrid search (combines keywords + persistent semantic vectors):
python -m whycode search . --query "how does response caching work" --mode hybrid

# Semantic vector search:
python -m whycode search . --query "sensitive file filters" --mode semantic
```

### 2. Ask Codebase Questions (RAG)
```powershell
python -m whycode ask . --question "How does WhyCode extract git commit evidence?"
```

### 3. Git History & Commit Summarization
```powershell
# List recent commits:
python -m whycode history . --limit 5

# Show raw git evidence for HEAD:
python -m whycode show . --commit HEAD

# Generate structured AI commit summary:
python -m whycode summarize . --commit HEAD
```
