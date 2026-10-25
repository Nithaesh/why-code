"""Symbol-level Git churn tracking: correlates code symbols with commit history."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Sequence

from whycode.git.history import CommitRecord, GitHistoryReader
from whycode.git.reader import GitCommitReader
from whycode.graph.ast_parser import CodeSymbol


@dataclass(frozen=True, slots=True)
class SymbolHistory:
    """Historical Git revisions and churn metrics for a specific code symbol."""

    symbol: CodeSymbol
    commits: tuple[CommitRecord, ...]
    churn_count: int
    last_modified_at: str | None
    last_author: str | None


class SymbolChurnTracker:
    """Trace Git commit history to specific functions, classes, and methods."""

    def __init__(
        self,
        repo_path: str | Path,
        history_reader: GitHistoryReader | None = None,
        commit_reader: GitCommitReader | None = None,
    ) -> None:
        self.repo_path = Path(repo_path).expanduser().resolve()
        self.history_reader = history_reader or GitHistoryReader(self.repo_path)
        self.commit_reader = commit_reader or GitCommitReader(self.repo_path)

    def trace_symbol(
        self,
        symbol: CodeSymbol,
        max_commits: int = 20,
    ) -> SymbolHistory:
        """Find commits that specifically modified lines within the symbol's span."""
        try:
            file_commits = self.history_reader.list_commits(
                limit=max_commits,
                path=symbol.file_path,
            )
        except Exception:
            file_commits = []

        matching_commits: list[CommitRecord] = []

        for record in file_commits:
            try:
                evidence = self.commit_reader.read_commit(record.commit_hash)
            except Exception:
                continue

            if self._diff_touches_span(evidence.diff, symbol.file_path, symbol.start_line, symbol.end_line):
                matching_commits.append(record)

        last_commit = matching_commits[0] if matching_commits else None
        return SymbolHistory(
            symbol=symbol,
            commits=tuple(matching_commits),
            churn_count=len(matching_commits),
            last_modified_at=last_commit.authored_at if last_commit else None,
            last_author=last_commit.author_name if last_commit else None,
        )

    def rank_churn(
        self,
        symbols: Sequence[CodeSymbol],
        max_commits_per_symbol: int = 15,
        top_n: int = 10,
    ) -> list[SymbolHistory]:
        """Rank symbols across the repository by modification frequency (churn)."""
        histories = [
            self.trace_symbol(sym, max_commits=max_commits_per_symbol)
            for sym in symbols
        ]
        # Sort descending by churn count, then by symbol name
        histories.sort(key=lambda h: (-h.churn_count, h.symbol.name))
        return histories[:top_n]

    @staticmethod
    def _diff_touches_span(
        diff: str,
        target_path: str,
        start_line: int,
        end_line: int,
    ) -> bool:
        """Inspect unified diff to determine if any hunk intersects [start_line, end_line]."""
        if not diff:
            return False

        # Pattern matches unified diff chunk header: @@ -old_start,old_count +new_start,new_count @@
        hunk_header_re = re.compile(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")

        for match in hunk_header_re.finditer(diff):
            new_start = int(match.group(3))
            new_count = int(match.group(4)) if match.group(4) is not None else 1
            new_end = new_start + max(0, new_count - 1)

            # Check overlap between [new_start, new_end] and [start_line, end_line]
            if max(new_start, start_line) <= min(new_end, end_line):
                return True

        return False
