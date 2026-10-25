
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

def test_search_command(tmp_path: Path, capsys) -> None:
    repo = make_repo(tmp_path)

    exit_code = main(
        ["search", str(repo), "--query", "greet"]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "hello.py" in output
    assert "greet" in output
    assert 'return "hello"' in output


def test_search_command_respects_top_k(
    tmp_path: Path,
    capsys,
) -> None:
    repo = make_repo(tmp_path)

    (repo / "another.py").write_text(
        "def greet_again():\n"
        '    return "hello again"\n',
        encoding="utf-8",
    )

    exit_code = main(
        [
            "search",
            str(repo),
            "--query",
            "greet",
            "--top-k",
            "1",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0

    # Only one search result should be printed.
    assert "1. " in output
    assert "2. " not in output


def test_search_command_with_no_matches(
    tmp_path: Path,
    capsys,
) -> None:
    repo = make_repo(tmp_path)

    exit_code = main(
        ["search", str(repo), "--query", "nonexistent_xyz"]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "No matching code found." in output


def test_ask_command_parser_supports_mode_flag() -> None:
    from whycode.__main__ import build_parser

    parser = build_parser()
    args = parser.parse_args(["ask", ".", "--question", "how does caching work?", "--mode", "hybrid", "--top-k", "3"])

    assert args.command == "ask"
    assert args.repo == "."
    assert args.question == "how does caching work?"
    assert args.mode == "hybrid"
    assert args.top_k == 3
