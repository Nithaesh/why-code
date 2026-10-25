from pathlib import Path
from unittest.mock import MagicMock

from whycode.agent.tools import InvestigationToolbox
from whycode.git.reader import ChangedFile, CommitEvidence
from whycode.graph.ast_parser import CodeSymbol
from whycode.graph.churn import SymbolHistory
from whycode.graph.service import SymbolInvestigationResult


def test_toolbox_search_code(tmp_path: Path):
    (tmp_path / "auth.py").write_text(
        "def authenticate(token):\n    return token == 'secret'\n",
        encoding="utf-8",
    )
    toolbox = InvestigationToolbox(repo_path=tmp_path)
    evidence = toolbox.search_code("authenticate")

    assert len(evidence) >= 1
    item = evidence[0]
    assert item.kind == "code_chunk"
    assert "auth.py" in item.source
    assert "authenticate" in item.content


def test_toolbox_inspect_symbol(tmp_path: Path):
    toolbox = InvestigationToolbox(repo_path=tmp_path)

    # Mock CodeGraphService inspect_symbol response
    defn = CodeSymbol(
        name="authenticate",
        qualified_name="auth.authenticate",
        kind="function",
        file_path="auth.py",
        start_line=1,
        end_line=2,
        docstring="Verify auth token.",
        calls=(),
        parameters=("token",),
    )
    caller = CodeSymbol(
        name="login_handler",
        qualified_name="server.login_handler",
        kind="function",
        file_path="server.py",
        start_line=10,
        end_line=15,
        docstring=None,
        calls=("authenticate",),
        parameters=(),
    )
    mock_result = SymbolInvestigationResult(
        query="authenticate",
        definitions=(defn,),
        callers=(caller,),
        callees=("check_hash",),
        histories=(),
    )
    toolbox.graph_service.inspect_symbol = MagicMock(return_value=mock_result)

    item = toolbox.inspect_symbol("authenticate")
    assert item.kind == "symbol_graph"
    assert item.source == "symbol:authenticate"
    assert "Definitions:" in item.content
    assert "auth.py:1-2" in item.content
    assert "login_handler" in item.content
    assert "check_hash" in item.content
    assert item.metadata["callers"] == ["login_handler"]


def test_toolbox_inspect_commit(tmp_path: Path):
    toolbox = InvestigationToolbox(repo_path=tmp_path)

    mock_commit = CommitEvidence(
        repo_root=str(tmp_path),
        commit_hash="abcdef1234567890",
        author_name="Alice Dev",
        author_email="alice@example.com",
        authored_at="2026-10-25 12:00:00 +0000",
        subject="Fix token expiry race condition",
        body="Shorten expiry and enforce monotonic clock.",
        changed_files=(ChangedFile(path="auth.py", status="M"),),
        diff="--- a/auth.py\n+++ b/auth.py\n@@ -1,2 +1,2 @@\n-expiry = 3600\n+expiry = 600\n",
        diff_truncated=False,
    )
    toolbox.commit_reader.read_commit = MagicMock(return_value=mock_commit)

    item = toolbox.inspect_commit("abcdef12")
    assert item is not None
    assert item.kind == "commit"
    assert item.source == "commit:abcdef12"
    assert "Fix token expiry" in item.summary
    assert "+expiry = 600" in item.content
    assert item.metadata["author"] == "Alice Dev"
    assert item.metadata["changed_files"] == ["auth.py"]


def test_toolbox_get_churn_hotspots(tmp_path: Path):
    toolbox = InvestigationToolbox(repo_path=tmp_path)

    sym = CodeSymbol(
        name="hot_func",
        qualified_name="hot_func",
        kind="function",
        file_path="hot.py",
        start_line=5,
        end_line=15,
        docstring=None,
        calls=(),
        parameters=(),
    )
    history = SymbolHistory(
        symbol=sym,
        commits=(),
        churn_count=8,
        last_modified_at=None,
        last_author=None,
    )
    toolbox.graph_service.get_churn_hotspots = MagicMock(return_value=[history])

    items = toolbox.get_churn_hotspots(top_n=1)
    assert len(items) == 1
    assert items[0].kind == "churn"
    assert items[0].source == "hotspot:hot_func"
    assert items[0].metadata["total_commits"] == 8
