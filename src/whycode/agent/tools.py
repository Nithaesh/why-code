"""Tools for agentic investigation across AST symbol graphs, vector search, and Git history."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Sequence

from whycode.agent.state import EvidenceItem
from whycode.git.reader import GitCommitReader, GitReaderError
from whycode.graph.service import CodeGraphService, SymbolInvestigationResult
from whycode.retrieval.service import CodebaseSearchService

logger = logging.getLogger(__name__)


class InvestigationToolbox:
    """Unified tool execution layer for repository investigation agents."""

    def __init__(
        self,
        repo_path: str | Path,
        search_service: CodebaseSearchService | None = None,
        graph_service: CodeGraphService | None = None,
        commit_reader: GitCommitReader | None = None,
    ) -> None:
        self.repo_path = Path(repo_path).expanduser().resolve()
        self.search_service = search_service or CodebaseSearchService(self.repo_path)
        self.graph_service = graph_service or CodeGraphService(self.repo_path)
        self.commit_reader = commit_reader or GitCommitReader(self.repo_path)

    def search_code(self, query: str, top_k: int = 5) -> list[EvidenceItem]:
        """Search repository source chunks via lexical/hybrid retrieval."""
        if not query or not query.strip():
            return []

        try:
            results = self.search_service.search(query=query, top_k=top_k)
        except Exception as exc:
            logger.warning("Code search failed for query '%s': %s", query, exc)
            return []

        evidence_items: list[EvidenceItem] = []
        for res in results:
            chunk = res.chunk
            source = f"{chunk.file_path}:{chunk.start_line}-{chunk.end_line}"
            summary = f"Code match for '{query}' in {chunk.file_path} (lines {chunk.start_line}-{chunk.end_line})"
            evidence_items.append(
                EvidenceItem(
                    kind="code_chunk",
                    source=source,
                    summary=summary,
                    content=chunk.content,
                    metadata={"path": chunk.file_path, "score": res.score},
                )
            )
        return evidence_items

    def inspect_symbol(self, symbol_name: str, max_commits: int = 5) -> EvidenceItem:
        """Inspect definition, callers, callees, and Git churn for an AST symbol."""
        cleaned = symbol_name.strip()
        result: SymbolInvestigationResult = self.graph_service.inspect_symbol(
            symbol_name=cleaned,
            include_history=True,
            max_commits=max_commits,
        )

        lines: list[str] = [f"Symbol: {cleaned}"]

        if result.definitions:
            lines.append("Definitions:")
            for d in result.definitions:
                lines.append(f"  - {d.kind} in {d.file_path}:{d.start_line}-{d.end_line}")
                if d.docstring:
                    lines.append(f"    Docstring: {d.docstring.strip()}")
        else:
            lines.append("Definitions: None found in repository AST.")

        if result.callers:
            lines.append("Callers (dependents):")
            for c in result.callers:
                lines.append(f"  - {c.name} ({c.kind} in {c.file_path}:{c.start_line})")
        else:
            lines.append("Callers (dependents): None detected in repository.")

        if result.callees:
            lines.append(f"Callees (dependencies): {', '.join(result.callees)}")
        else:
            lines.append("Callees (dependencies): None")

        if result.histories:
            lines.append("Git Churn History:")
            for h in result.histories:
                lines.append(f"  - Total commits touching symbol: {h.churn_count}")
                for c in h.commits[:max_commits]:
                    lines.append(f"    * commit {c.commit_hash[:8]}: {c.subject} ({c.authored_at})")
        else:
            lines.append("Git Churn History: No commit modifications detected.")

        content = "\n".join(lines)
        defn_count = len(result.definitions)
        caller_count = len(result.callers)
        total_churn = sum(h.churn_count for h in result.histories)
        summary = (
            f"Symbol '{cleaned}': {defn_count} definitions, {caller_count} callers, "
            f"{total_churn} commit revisions."
        )

        return EvidenceItem(
            kind="symbol_graph",
            source=f"symbol:{cleaned}",
            summary=summary,
            content=content,
            metadata={
                "symbol": cleaned,
                "definitions": [f"{d.file_path}:{d.start_line}" for d in result.definitions],
                "callers": [c.name for c in result.callers],
                "callees": list(result.callees),
            },
        )

    def inspect_commit(self, commit_hash: str) -> EvidenceItem | None:
        """Inspect unified diff and metadata for a specific Git commit."""
        cleaned = commit_hash.strip()
        try:
            commit = self.commit_reader.read_commit(cleaned)
        except (GitReaderError, Exception) as exc:
            logger.warning("Could not read commit %s: %s", cleaned, exc)
            return None

        changed_paths = [f.path for f in commit.changed_files]
        lines = [
            f"Commit: {commit.commit_hash}",
            f"Author: {commit.author_name} <{commit.author_email}>",
            f"Date:   {commit.authored_at}",
            f"Subject: {commit.subject}",
        ]
        if commit.body:
            lines.append(f"Body: {commit.body}")
        lines.append(f"Changed Files ({len(changed_paths)}): {', '.join(changed_paths)}")
        lines.append("\nDiff:")
        lines.append(commit.diff if commit.diff else "(Empty diff)")

        content = "\n".join(lines)
        summary = f"Commit {commit.commit_hash[:8]}: {commit.subject} ({len(changed_paths)} files changed)"

        return EvidenceItem(
            kind="commit",
            source=f"commit:{commit.commit_hash[:8]}",
            summary=summary,
            content=content,
            metadata={
                "commit_hash": commit.commit_hash,
                "author": commit.author_name,
                "date": commit.authored_at,
                "changed_files": changed_paths,
            },
        )

    def get_churn_hotspots(self, top_n: int = 5) -> list[EvidenceItem]:
        """Identify code symbols undergoing the most frequent changes."""
        try:
            hotspots = self.graph_service.get_churn_hotspots(top_n=top_n)
        except Exception as exc:
            logger.warning("Failed to calculate churn hotspots: %s", exc)
            return []

        evidence_items: list[EvidenceItem] = []
        for h in hotspots:
            s = h.symbol
            summary = f"Hotspot '{s.name}': {h.churn_count} revisions across Git history"
            content = (
                f"Symbol: {s.name} ({s.kind})\n"
                f"File: {s.file_path}:{s.start_line}-{s.end_line}\n"
                f"Total Revisions: {h.churn_count}\n"
                f"Recent Commits:\n"
                + "\n".join(
                    f"  - {c.commit_hash[:8]} ({c.authored_at}): {c.subject}"
                    for c in h.commits[:5]
                )
            )
            evidence_items.append(
                EvidenceItem(
                    kind="churn",
                    source=f"hotspot:{s.name}",
                    summary=summary,
                    content=content,
                    metadata={"symbol": s.name, "total_commits": h.churn_count},
                )
            )
        return evidence_items
