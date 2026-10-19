
import subprocess
from pathlib import Path

from whycode.__main__ import main


def run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "cli-repo"
    repo.mkdir()

    run_git(repo, "init", "-q")
    run_git(repo, "config", "user.name", "CLI Test")
    run_git(repo, "config", "user.email", "cli@example.com")

    (repo / "hello.py").write_text(
        'def greet():\n    return "hello"\n',
        encoding="utf-8",
    )
    run_git(repo, "add", "hello.py")
    run_git(repo, "commit", "-m", "Add greeting")

    return repo


def test_history_command(tmp_path: Path, capsys) -> None:
    repo = make_repo(tmp_path)

    exit_code = main(["history", str(repo)])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Add greeting" in output
    assert "CLI Test" in output


def test_show_command(tmp_path: Path, capsys) -> None:
    repo = make_repo(tmp_path)

    exit_code = main(["show", str(repo)])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Add greeting" in output
    assert "hello.py" in output
    assert 'return "hello"' in output


def test_history_rejects_invalid_limit(
    tmp_path: Path,
    capsys,
) -> None:
    repo = make_repo(tmp_path)

    exit_code = main(["history", str(repo), "--limit", "0"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "limit must be positive" in captured.err
