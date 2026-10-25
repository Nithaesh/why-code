"""Coordination service linking AST symbol extraction, dependency graph, and Git churn."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from whycode.graph.ast_parser import ASTSymbolParser, CodeSymbol, FileModuleInfo
from whycode.graph.churn import SymbolChurnTracker, SymbolHistory
from whycode.graph.dependency import CodebaseGraph
from whycode.ingest.scanner import RepositoryScanner, SourceFile


@dataclass(frozen=True, slots=True)
class SymbolInvestigationResult:
    """Complete structural and historical diagnostic for a code symbol."""

    query: str
    definitions: tuple[CodeSymbol, ...]
    callers: tuple[CodeSymbol, ...]
    callees: tuple[str, ...]
    histories: tuple[SymbolHistory, ...]


class CodeGraphService:
    """Build and query the repository-wide AST symbol graph and Git churn history."""

    def __init__(
        self,
        repo_path: str | Path,
        scanner: RepositoryScanner | None = None,
        parser: ASTSymbolParser | None = None,
        churn_tracker: SymbolChurnTracker | None = None,
    ) -> None:
        self.repo_path = Path(repo_path).expanduser().resolve()
        self.scanner = scanner or RepositoryScanner(self.repo_path)
        self.parser = parser or ASTSymbolParser()
        self.churn_tracker = churn_tracker or SymbolChurnTracker(self.repo_path)
        self._graph: CodebaseGraph | None = None

    def get_graph(self, force_refresh: bool = False) -> CodebaseGraph:
        """Lazily construct or refresh the codebase symbol graph."""
        if self._graph is not None and not force_refresh:
            return self._graph

        source_files: list[SourceFile] = self.scanner.scan()
        modules: list[FileModuleInfo] = []

        for sf in source_files:
            if not sf.path.endswith(".py"):
                continue
            abs_path = self.repo_path / sf.path
            info = self.parser.parse_file(file_path=abs_path, repo_root=self.repo_path)
            modules.append(info)

        self._graph = CodebaseGraph(modules)
        return self._graph

    def inspect_symbol(
        self,
        symbol_name: str,
        include_history: bool = True,
        max_commits: int = 15,
    ) -> SymbolInvestigationResult:
        """Deep investigation of a symbol: definition, callers, callees, and Git churn."""
        graph = self.get_graph()
        definitions = graph.find_symbols(symbol_name)
        callers = graph.get_callers(symbol_name)
        callees = graph.get_callees(symbol_name)

        histories: list[SymbolHistory] = []
        if include_history and definitions:
            for defn in definitions:
                hist = self.churn_tracker.trace_symbol(defn, max_commits=max_commits)
                histories.append(hist)

        return SymbolInvestigationResult(
            query=symbol_name,
            definitions=tuple(definitions),
            callers=tuple(callers),
            callees=tuple(callees),
            histories=tuple(histories),
        )

    def get_churn_hotspots(
        self,
        top_n: int = 10,
        max_commits: int = 15,
    ) -> list[SymbolHistory]:
        """Identify functions/classes with the highest modification frequency in Git history."""
        graph = self.get_graph()
        all_symbols = graph.get_all_symbols()
        # Filter down to top-level functions and classes for meaningful hotspot analysis
        analyzed_symbols = [s for s in all_symbols if s.kind in ("class", "function")]
        try:
            return self.churn_tracker.rank_churn(
                symbols=analyzed_symbols,
                max_commits_per_symbol=max_commits,
                top_n=top_n,
            )
        except Exception:
            return []
