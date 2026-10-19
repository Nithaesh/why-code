
import subprocess
from pathlib import Path

import pytest

from whycode.git.reader import CommitEvidence
from whycode.investigation import CommitInvestigationService
from whycode.summarizer.models import CommitSummary


def run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


@pytest.fixture
def investigation_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "investigation-repo"
    repo.mkdir()

    run_git(repo, "init", "-q")
    run_git(repo, "config", "user.name", "Investigation Test")
    run_git(repo, "config", "user.email", "investigation@example.com")

    (repo / "hello.py").write_text(
        'def greet():\n    return "hello"\n',
        encoding="utf-8",
    )
    run_git(repo, "add", "hello.py")
    run_git(repo, "commit", "-m", "Add greeting")

    (repo / "hello.py").write_text(
        'def greet():\n    return "hello, world"\n',
        encoding="utf-8",
    )
    run_git(repo, "add", "hello.py")
    run_git(repo, "commit", "-m", "Update greeting")

    (repo / "other.py").write_text(
        "VALUE = 42\n",
        encoding="utf-8",
    )
    run_git(repo, "add", "other.py")
    run_git(repo, "commit", "-m", "Add other module")

    return repo


class FakeSummaryService:
    def __init__(self) -> None:
        self.received_evidence = None

    def summarize(self, evidence: CommitEvidence) -> CommitSummary:
        self.received_evidence = evidence
        return CommitSummary(
            summary="Adds a module containing a constant.",
            changes=["Adds VALUE with the value 42."],
            likely_purpose="To define a constant for later use.",
            evidence=[],
            uncertainties=[
                "The commit does not establish how the constant is used."
            ],
        )


def test_investigates_commit_end_to_end(
    investigation_repo: Path,
) -> None:
    fake_summary = FakeSummaryService()
    service = CommitInvestigationService(
        investigation_repo,
        summary_service=fake_summary,
    )

    result = service.investigate()

    assert result.evidence.subject == "Add other module"
    assert result.summary.summary == (
        "Adds a module containing a constant."
    )
    assert len(result.recent_history) == 3
    assert result.recent_history[0].subject == "Add other module"
    assert fake_summary.received_evidence == result.evidence


def test_investigates_a_selected_commit(
    investigation_repo: Path,
) -> None:
    fake_summary = FakeSummaryService()
    service = CommitInvestigationService(
        investigation_repo,
        summary_service=fake_summary,
    )
    selected_hash = run_git(
        investigation_repo, "rev-parse", "HEAD~1"
    )

    result = service.investigate(commit_ref=selected_hash)

    assert result.evidence.commit_hash == selected_hash
    assert result.evidence.subject == "Update greeting"
    assert result.summary is not None


def test_filters_recent_history_by_path(
    investigation_repo: Path,
) -> None:
    service = CommitInvestigationService(
        investigation_repo,
        summary_service=FakeSummaryService(),
    )

    result = service.investigate(path="hello.py")

    assert [record.subject for record in result.recent_history] == [
        "Update greeting",
        "Add greeting",
    ]
    # The selected commit is still HEAD, even though it changed other.py.
    assert result.evidence.subject == "Add other module"


def test_rejects_nonpositive_history_limit(
    investigation_repo: Path,
) -> None:
    with pytest.raises(ValueError, match="history_limit"):
        CommitInvestigationService(
            investigation_repo,
            summary_service=FakeSummaryService(),
            history_limit=0,
        )
