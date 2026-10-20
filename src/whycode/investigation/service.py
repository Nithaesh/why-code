
from dataclasses import dataclass
from pathlib import Path

from whycode.git.history import CommitRecord, GitHistoryReader
from whycode.git.reader import CommitEvidence, GitCommitReader
from whycode.summarizer.models import CommitSummary
from whycode.summarizer.service import CommitSummaryService


@dataclass(frozen=True)
class CommitInvestigation:
    """Combined history, detailed evidence, and summary for a commit."""

    recent_history: tuple[CommitRecord, ...]
    evidence: CommitEvidence
    summary: CommitSummary


class CommitInvestigationService:
    """Connect Git history, commit evidence, and commit summarization."""

    def __init__(
        self,
        repo_path: str | Path,
        summary_service: CommitSummaryService,
        history_limit: int = 10,
        timeout_seconds: int = 10,
    ) -> None:
        if history_limit <= 0:
            raise ValueError("history_limit must be positive.")

        self.history_limit = history_limit
        self.history_reader = GitHistoryReader(
            repo_path,
            timeout_seconds=timeout_seconds,
        )
        self.commit_reader = GitCommitReader(
            repo_path,
            timeout_seconds=timeout_seconds,
        )
        self.summary_service = summary_service

    def investigate(
        self,
        commit_ref: str = "HEAD",
        path: str | None = None,
    ) -> CommitInvestigation:
        """Collect recent history and summarize the selected commit."""
        history = self.history_reader.list_commits(
            limit=self.history_limit,
            path=path,
        )

        evidence = self.commit_reader.read_commit(commit_ref)

        summary = self.summary_service.summarize(evidence)

        return CommitInvestigation(
            recent_history=tuple(history),
            evidence=evidence,
            summary=summary,
        )
