from pathlib import Path
from unittest.mock import MagicMock

from whycode.__main__ import build_parser, main
from whycode.graph.service import CodeGraphService


def test_inspect_symbol_end_to_end(tmp_path: Path) -> None:
    # Create sample repository files
    (tmp_path / "calc.py").write_text(
        "def add(a, b):\n"
        "    return a + b\n",
        encoding="utf-8",
    )
    (tmp_path / "main.py").write_text(
        "from calc import add\n"
        "\n"
        "def run():\n"
        "    result = add(2, 3)\n"
        "    return result\n",
        encoding="utf-8",
    )

    service = CodeGraphService(tmp_path)
    # Mock churn_tracker trace_symbol to avoid needing a live git repo in this unit test
    service.churn_tracker.trace_symbol = MagicMock(return_value=MagicMock(
        symbol=MagicMock(name="add"),
        commits=(),
        churn_count=0,
    ))

    result = service.inspect_symbol("add")

    assert result.query == "add"
    assert len(result.definitions) == 1
    assert result.definitions[0].file_path == "calc.py"
    assert result.definitions[0].start_line == 1
    assert len(result.callers) == 1
    assert result.callers[0].name == "run"
    assert result.callers[0].file_path == "main.py"


def test_cli_symbol_and_churn_commands(tmp_path: Path, capsys) -> None:
    (tmp_path / "util.py").write_text(
        "def format_str(s):\n"
        "    return s.strip()\n",
        encoding="utf-8",
    )

    # Test symbol command
    exit_code = main(["symbol", str(tmp_path), "--name", "format_str"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "format_str" in output
    assert "util.py" in output

    # Test churn command
    exit_code_churn = main(["churn", str(tmp_path), "--limit", "5"])
    output_churn = capsys.readouterr().out

    assert exit_code_churn == 0
    assert "Top" in output_churn or "Hotspots" in output_churn
