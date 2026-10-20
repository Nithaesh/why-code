
import subprocess
from pathlib import Path

import pytest

from whycode.git.reader import GitCommitReader, GitReaderError


def run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


@pytest.fixture
def sample_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "sample-repo"
    repo.mkdir()

    run_git(repo, "init", "-q")
    run_git(repo, "config", "user.name", "WhyCode Test")
    run_git(repo, "config", "user.email", "whycode-test@example.com")

    (repo / "hello.py").write_text(
        'def greet():\n    return "hello"\n',
        encoding="utf-8",
    )
    run_git(repo, "add", "hello.py")
    run_git(repo, "commit", "-m", "Add greeting function")

    return repo


def test_reads_commit_metadata_and_added_file(sample_repo: Path) -> None:
    evidence = GitCommitReader(sample_repo).read_commit()

    assert evidence.commit_hash == run_git(
        sample_repo, "rev-parse", "HEAD"
    )
    assert evidence.subject == "Add greeting function"
    assert evidence.author_name == "WhyCode Test"
    assert evidence.repo_root == str(sample_repo.resolve())

    assert len(evidence.changed_files) == 1
    assert evidence.changed_files[0].path == "hello.py"
    assert evidence.changed_files[0].status == "A"

    assert 'return "hello"' in evidence.diff
    assert evidence.diff_truncated is False


def test_rejects_unknown_commit(sample_repo: Path) -> None:
    with pytest.raises(GitReaderError):
        GitCommitReader(sample_repo).read_commit(
            "this-commit-does-not-exist"
        )


def test_reports_when_diff_is_truncated(sample_repo: Path) -> None:
    reader = GitCommitReader(sample_repo, max_diff_chars=10)
    evidence = reader.read_commit()

    assert len(evidence.diff) == 10
    assert evidence.diff_truncated is True
