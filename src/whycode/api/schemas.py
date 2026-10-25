"""Pydantic request and response schemas for the WhyCode REST API."""

from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    repo_path: str
    provider: str
    model: str
    has_api_key: bool


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Keywords or query text to search for")
    top_k: int = Field(default=5, ge=1, le=50, description="Maximum number of code chunks to return")
    mode: Literal["lexical", "hybrid", "semantic"] = Field(
        default="hybrid", description="Retrieval mode"
    )
    reindex: bool = Field(default=False, description="Whether to force re-indexing")


class CodeChunkItem(BaseModel):
    chunk_id: str
    file_path: str
    start_line: int
    end_line: int
    content: str
    score: float


class SearchResponse(BaseModel):
    query: str
    mode: str
    total_results: int
    results: list[CodeChunkItem]


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Question to answer using repository code")
    top_k: int = Field(default=5, ge=1, le=20, description="Code chunks to retrieve as context")
    mode: Literal["hybrid", "lexical", "semantic"] = Field(
        default="hybrid", description="Retrieval mode"
    )


class SourceReferenceItem(BaseModel):
    file_path: str
    start_line: int
    end_line: int
    chunk_id: str


class CitationVerificationItem(BaseModel):
    raw_citation: str
    is_verified: bool
    reason: str


class AskResponse(BaseModel):
    question: str
    answer: str
    grounding_confidence: float
    sources: list[SourceReferenceItem]
    verified_citations: list[CitationVerificationItem]
    context_truncated: bool


class SymbolDefinitionItem(BaseModel):
    name: str
    qualified_name: str
    kind: str
    file_path: str
    start_line: int
    end_line: int
    docstring: str | None = None
    parameters: list[str] = Field(default_factory=list)


class SymbolCallerItem(BaseModel):
    name: str
    qualified_name: str
    kind: str
    file_path: str
    start_line: int


class SymbolCommitItem(BaseModel):
    commit_hash: str
    author_name: str
    authored_at: str
    subject: str


class SymbolHistoryItem(BaseModel):
    symbol_name: str
    churn_count: int
    last_modified_at: str | None = None
    last_author: str | None = None
    commits: list[SymbolCommitItem] = Field(default_factory=list)


class SymbolDetailResponse(BaseModel):
    query: str
    definitions: list[SymbolDefinitionItem]
    callers: list[SymbolCallerItem]
    callees: list[str]
    histories: list[SymbolHistoryItem]


class ChurnHotspotItem(BaseModel):
    rank: int
    symbol_name: str
    kind: str
    file_path: str
    start_line: int
    churn_count: int
    recent_commits: list[SymbolCommitItem] = Field(default_factory=list)


class ChurnHotspotsResponse(BaseModel):
    total: int
    hotspots: list[ChurnHotspotItem]


class InvestigateRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Diagnostic software archaeology inquiry")
    max_steps: int = Field(default=3, ge=1, le=10, description="Max reasoning iterations")


class InvestigateResponse(BaseModel):
    query: str
    summary: str
    timeline: list[str]
    root_causes: list[str]
    affected_symbols: list[str]
    citations: list[str]
    uncertainties: list[str]
    raw_markdown: str
