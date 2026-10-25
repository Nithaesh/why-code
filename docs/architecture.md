# WhyCode Architecture Overview (Phases 0–4)

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
│   ├── context.py        # ContextBuilder (evidence formatting)
│   ├── qa.py             # QuestionAnsweringService (grounded code Q&A)
│   └── service.py        # CodebaseSearchService (search coordinator)
├── summarizer/           # Structured commit analysis
│   ├── models.py         # CommitSummary, EvidenceItem Pydantic schemas
│   └── service.py        # CommitSummaryService (hallucination defense)
└── investigation/        # High-level investigation coordination
    └── service.py        # CommitInvestigationService
```

## Persistent Vector & Hybrid Search Architecture (Phase 4)

1. **Storage Subsystem (`VectorIndex`):**
   - SQLite relational tables: `indexed_files` (stores file path, content hash, mtime, chunk count) and `chunks` (chunk_id, line boundaries, content, binary float32 BLOB embedding).
   - Fast deserialization using `np.frombuffer(blob, dtype=np.float32)`.

2. **Synchronization Subsystem (`IndexSynchronizer`):**
   - Change-aware indexing: compares SHA-256 hash of on-disk file content against `indexed_files`.
   - Untouched files are skipped, saving embedding API calls and compute.
   - Modified and new files are chunked and embedded. Deleted files are purged via foreign key cascade.

3. **Reciprocal Rank Fusion (`HybridRetriever`):**
   - Combines lexical rankings and dense vector cosine similarity rankings without raw score calibration issues:
     $$RRF(d) = \sum_{m \in \{\text{lexical}, \text{vector}\}} \frac{w_m}{k + \text{rank}_m(d)}$$
   - Standard constant $k=60$, with tie-breaking based on file path and line position.

4. **Retrieval Evaluation Subsystem (`eval/`):**
   - Benchmark dataset measuring Hit@1, Hit@3, Hit@5, and Mean Reciprocal Rank (MRR).


## Grounded Hybrid RAG & Verification Architecture (Phase 5)

```
User Question
    │
    ▼
CodebaseSearchService (Hybrid: Lexical BM25 + Persistent Vector Index)
    │
    ▼
Candidate Chunks (Top-K)
    │
    ▼
ContextDistiller
    ├─ Merges adjacent/overlapping chunks from the same file into unified line spans
    └─ Enforces context size ceiling (max_context_chars)
    │
    ▼
CachedLLM (using code_qa.md prompt)
    ├─ Untrusted repository evidence context framing
    └─ Generation with zero temperature
    │
    ▼
CitationVerifier
    ├─ Extracts cited sources ([Source N], file.py:start-end)
    ├─ Cross-references against distilled evidence spans
    ├─ Detects hallucinated files or out-of-bound line ranges
    └─ Computes Grounding Confidence Score
    │
    ▼
QuestionAnswer Model (Answer + Sources + Verified Citations + Grounding Confidence)
```


## Repository Structure & Git-History Association (Phase 6)

```
                     Python Source Files (.py)
                                │
                                ▼
                       ASTSymbolParser (ast)
                                │
         ┌──────────────────────┴──────────────────────┐
         ▼                                             ▼
Definitions (Classes, Functions, Methods)       Call & Import Edges
         │                                             │
         └──────────────────────┬──────────────────────┘
                                ▼
                         CodebaseGraph
             (find_symbols, get_callers, get_callees)
                                │
                                ▼
                       SymbolChurnTracker
              (Git Commit Diffs vs Symbol Line Spans)
                                │
                                ▼
                        CodeGraphService
             (inspect_symbol, get_churn_hotspots)
                                │
         ┌──────────────────────┴──────────────────────┐
         ▼                                             ▼
   CLI `whycode symbol`                         CLI `whycode churn`
(Definitions, Callers, History)                 (Hotspot Churn Ranking)
```
