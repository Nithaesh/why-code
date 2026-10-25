"""FastAPI application factory and middleware configuration for WhyCode."""

from __future__ import annotations

import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from whycode.agent import InvestigationAgent, InvestigationToolbox
from whycode.api.routes import router
from whycode.config import Settings
from whycode.graph.service import CodeGraphService
from whycode.llm.base import BaseLLM
from whycode.llm.cache import DiskCache
from whycode.llm.client import CachedLLM
from whycode.llm.embedding import BaseEmbedder
from whycode.llm.gemini import GeminiProvider
from whycode.retrieval.qa import QuestionAnsweringService
from whycode.retrieval.service import CodebaseSearchService

logger = logging.getLogger(__name__)


def create_app(
    repo_path: str | Path | None = None,
    llm: BaseLLM | None = None,
    embedder: BaseEmbedder | None = None,
    settings: Settings | None = None,
) -> FastAPI:
    """Create and configure a WhyCode FastAPI application instance."""
    app = FastAPI(
        title="WhyCode API",
        description="Evidence-backed codebase history investigation, hybrid retrieval, and agentic diagnostics.",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Enable CORS for developer convenience (VS Code extensions, web dashboards)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Resolve settings and repository path
    current_settings = settings or Settings()
    resolved_repo = Path(repo_path or Path.cwd()).expanduser().resolve()

    # Lazily initialize default LLM if not supplied
    active_llm = llm
    if active_llm is None:
        try:
            api_key = current_settings.require_gemini_key()
            provider = GeminiProvider(
                api_key=api_key,
                model=current_settings.gemini_model,
            )
            cache = DiskCache(current_settings.whycode_cache_dir)
            active_llm = CachedLLM(
                provider=provider,
                cache=cache,
                provider_name=current_settings.whycode_provider,
                model=current_settings.gemini_model,
            )
        except Exception as exc:
            logger.info("Default LLM provider not configured: %s", exc)
            active_llm = None

    # Construct subsystem services
    search_service = CodebaseSearchService(repo_path=resolved_repo, embedder=embedder)
    graph_service = CodeGraphService(repo_path=resolved_repo)
    toolbox = InvestigationToolbox(
        repo_path=resolved_repo,
        search_service=search_service,
        graph_service=graph_service,
    )

    qa_service = None
    if active_llm is not None:
        qa_service = QuestionAnsweringService(
            repo_path=resolved_repo,
            llm=active_llm,
            embedder=embedder,
            search_service=search_service,
        )

    def agent_factory(max_steps: int = 3) -> InvestigationAgent:
        if active_llm is None:
            raise RuntimeError("LLM is required for agentic investigation.")
        return InvestigationAgent(
            llm=active_llm,
            toolbox=toolbox,
            max_iterations=max_steps,
        )

    # Store services in application state for route dependency injection
    app.state.services = {
        "repo_path": resolved_repo,
        "settings": current_settings,
        "llm": active_llm,
        "embedder": embedder,
        "search_service": search_service,
        "graph_service": graph_service,
        "qa_service": qa_service,
        "toolbox": toolbox,
        "agent_factory": agent_factory,
    }

    app.include_router(router)

    # Mount static frontend if web/ directory exists
    web_dir = Path(__file__).resolve().parents[3] / "web"
    if web_dir.exists():
        app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="web")

    return app
