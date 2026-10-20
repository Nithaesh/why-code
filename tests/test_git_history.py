
import subprocess
from pathlib import Path

import pytest

from whycode.git import GitHistoryReader


def run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


@pytest.fixture
def history_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "history-repo"
    repo.mkdir()

    run_git(repo, "init", "-q")
    run_git(repo, "config", "user.name", "History Test")
    run_git(repo, "config", "user.email", "history@example.com")

    (repo / "hello.py").write_text(
        'def greet():\n    return "hello"\n',
        encoding="utf-8",
    )
    run_git(repo, "add", "hello.py")
    run_git(repo, "commit", "-m", "Add greeting function")

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


def test_lists_commits_newest_first(history_repo: Path) -> None:
    records = GitHistoryReader(history_repo).list_commits()

    assert [record.subject for record in records] == [
        "Add other module",
        "Update greeting",
        "Add greeting function",
    ]
    assert all(record.commit_hash for record in records)


def test_respects_limit(history_repo: Path) -> None:
    records = GitHistoryReader(history_repo).list_commits(limit=2)

    assert len(records) == 2
    assert records[0].subject == "Add other module"


def test_filters_by_file_path(history_repo: Path) -> None:
    records = GitHistoryReader(history_repo).list_commits(
        path="hello.py"
    )

    assert [record.subject for record in records] == [
        "Update greeting",
        "Add greeting function",
    ]


def test_rejects_nonpositive_limit(history_repo: Path) -> None:
    with pytest.raises(ValueError, match="limit"):
        GitHistoryReader(history_repo).list_commits(limit=0)


def test_rejects_parent_directory_path(history_repo: Path) -> None:
    with pytest.raises(ValueError, match="repository-relative"):
        GitHistoryReader(history_repo).list_commits(path="../secret.txt")
