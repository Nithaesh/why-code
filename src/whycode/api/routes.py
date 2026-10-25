"""FastAPI router endpoints exposing WhyCode intelligence services."""

from __future__ import annotations

import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from whycode.api.schemas import (
    AskRequest,
    AskResponse,
    ChurnHotspotItem,
    ChurnHotspotsResponse,
    CitationVerificationItem,
    CodeChunkItem,
    HealthResponse,
    InvestigateRequest,
    InvestigateResponse,
    SearchRequest,
    SearchResponse,
    SourceReferenceItem,
    SymbolCallerItem,
    SymbolCommitItem,
    SymbolDefinitionItem,
    SymbolDetailResponse,
    SymbolHistoryItem,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["WhyCode API"])


def get_services(request: Request) -> dict[str, Any]:
    """Retrieve injected services container from application state."""
    return getattr(request.app.state, "services", {})


@router.get("/health", response_model=HealthResponse)
def health_check(services: dict[str, Any] = Depends(get_services)) -> HealthResponse:
    """Return health status, configured provider, and active repository information."""
    settings = services.get("settings")
    repo_path = str(services.get("repo_path", ""))
    provider = settings.whycode_provider if settings else "none"
    model = settings.gemini_model if settings else "none"
    has_api_key = bool(settings and settings.gemini_api_key.get_secret_value().strip())

    return HealthResponse(
        status="ok",
        version="0.1.0",
        repo_path=repo_path,
        provider=provider,
        model=model,
        has_api_key=has_api_key,
    )


@router.post("/search", response_model=SearchResponse)
def search_code(
    payload: SearchRequest,
    services: dict[str, Any] = Depends(get_services),
) -> SearchResponse:
    """Perform lexical, vector, or hybrid search across repository code chunks."""
    search_service = services.get("search_service")
    if not search_service:
        raise HTTPException(status_code=500, detail="Search service is not initialized.")

    try:
        results = search_service.search(
            query=payload.query,
            top_k=payload.top_k,
            mode=payload.mode,
            force_sync=payload.reindex,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Search execution failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Search failed: {exc}")

    items = [
        CodeChunkItem(
            chunk_id=r.chunk.chunk_id,
            file_path=r.chunk.file_path,
            start_line=r.chunk.start_line,
            end_line=r.chunk.end_line,
            content=r.chunk.content,
            score=r.score,
        )
        for r in results
    ]

    return SearchResponse(
        query=payload.query,
        mode=payload.mode,
        total_results=len(items),
        results=items,
    )


@router.post("/ask", response_model=AskResponse)
def ask_question(
    payload: AskRequest,
    services: dict[str, Any] = Depends(get_services),
) -> AskResponse:
    """Answer questions about repository code with grounded citations and confidence."""
    qa_service = services.get("qa_service")
    if not qa_service:
        raise HTTPException(status_code=500, detail="Question answering service is not initialized.")

    try:
        ans = qa_service.ask(
            question=payload.question,
            top_k=payload.top_k,
            mode=payload.mode,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Question answering failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Q&A failed: {exc}")

    sources = [
        SourceReferenceItem(
            file_path=s.file_path,
            start_line=s.start_line,
            end_line=s.end_line,
            chunk_id=s.chunk_id,
        )
        for s in ans.sources
    ]

    verified = [
        CitationVerificationItem(
            raw_citation=v.raw_citation,
            is_verified=v.is_verified,
            reason=v.reason,
        )
        for v in ans.verified_citations
    ]

    return AskResponse(
        question=ans.question,
        answer=ans.answer,
        grounding_confidence=ans.grounding_confidence,
        sources=sources,
        verified_citations=verified,
        context_truncated=ans.context_truncated,
    )


@router.get("/symbol/{name}", response_model=SymbolDetailResponse)
def inspect_symbol(
    name: str,
    max_commits: int = Query(default=10, ge=1, le=50),
    services: dict[str, Any] = Depends(get_services),
) -> SymbolDetailResponse:
    """Inspect AST definitions, callers, callees, and Git churn for a code symbol."""
    graph_service = services.get("graph_service")
    if not graph_service:
        raise HTTPException(status_code=500, detail="Code graph service is not initialized.")

    try:
        res = graph_service.inspect_symbol(
            symbol_name=name,
            include_history=True,
            max_commits=max_commits,
        )
    except Exception as exc:
        logger.exception("Symbol inspection failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Symbol inspection failed: {exc}")

    definitions = [
        SymbolDefinitionItem(
            name=d.name,
            qualified_name=d.qualified_name,
            kind=d.kind,
            file_path=d.file_path,
            start_line=d.start_line,
            end_line=d.end_line,
            docstring=d.docstring,
            parameters=list(d.parameters),
        )
        for d in res.definitions
    ]

    callers = [
        SymbolCallerItem(
            name=c.name,
            qualified_name=c.qualified_name,
            kind=c.kind,
            file_path=c.file_path,
            start_line=c.start_line,
        )
        for c in res.callers
    ]

    histories: list[SymbolHistoryItem] = []
    for h in res.histories:
        commit_items = [
            SymbolCommitItem(
                commit_hash=c.commit_hash,
                author_name=c.author_name,
                authored_at=c.authored_at,
                subject=c.subject,
            )
            for c in h.commits
        ]
        histories.append(
            SymbolHistoryItem(
                symbol_name=h.symbol.name,
                churn_count=h.churn_count,
                last_modified_at=h.last_modified_at,
                last_author=h.last_author,
                commits=commit_items,
            )
        )

    return SymbolDetailResponse(
        query=res.query,
        definitions=definitions,
        callers=callers,
        callees=list(res.callees),
        histories=histories,
    )


@router.get("/churn", response_model=ChurnHotspotsResponse)
def get_churn_hotspots(
    limit: int = Query(default=10, ge=1, le=50),
    services: dict[str, Any] = Depends(get_services),
) -> ChurnHotspotsResponse:
    """Identify codebase churn hotspots based on Git modification frequency."""
    graph_service = services.get("graph_service")
    if not graph_service:
        raise HTTPException(status_code=500, detail="Code graph service is not initialized.")

    try:
        hotspots = graph_service.get_churn_hotspots(top_n=limit)
    except Exception as exc:
        logger.exception("Churn calculation failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Churn calculation failed: {exc}")

    items: list[ChurnHotspotItem] = []
    for rank, h in enumerate(hotspots, start=1):
        commits = [
            SymbolCommitItem(
                commit_hash=c.commit_hash,
                author_name=c.author_name,
                authored_at=c.authored_at,
                subject=c.subject,
            )
            for c in h.commits[:5]
        ]
        items.append(
            ChurnHotspotItem(
                rank=rank,
                symbol_name=h.symbol.name,
                kind=h.symbol.kind,
                file_path=h.symbol.file_path,
                start_line=h.symbol.start_line,
                churn_count=h.churn_count,
                recent_commits=commits,
            )
        )

    return ChurnHotspotsResponse(total=len(items), hotspots=items)


@router.post("/investigate", response_model=InvestigateResponse)
def investigate(
    payload: InvestigateRequest,
    services: dict[str, Any] = Depends(get_services),
) -> InvestigateResponse:
    """Run an autonomous agentic multi-hop investigation across AST, Git, and search."""
    agent_factory = services.get("agent_factory")
    if not agent_factory:
        raise HTTPException(status_code=500, detail="Investigation agent is not initialized.")

    try:
        agent = agent_factory(max_steps=payload.max_steps)
        report = agent.investigate(query=payload.query)
    except Exception as exc:
        logger.exception("Agentic investigation failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Investigation failed: {exc}")

    return InvestigateResponse(
        query=report.query,
        summary=report.summary,
        timeline=report.timeline,
        root_causes=report.root_causes,
        affected_symbols=report.affected_symbols,
        citations=report.citations,
        uncertainties=report.uncertainties,
        raw_markdown=report.raw_markdown,
    )
