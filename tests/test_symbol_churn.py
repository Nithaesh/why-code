from pathlib import Path
from unittest.mock import MagicMock

from whycode.git.history import CommitRecord
from whycode.git.reader import ChangedFile, CommitEvidence
from whycode.graph.ast_parser import CodeSymbol
from whycode.graph.churn import SymbolChurnTracker


def _make_sym(name: str, file_path: str, start: int, end: int) -> CodeSymbol:
    return CodeSymbol(
        name=name,
        qualified_name=name,
        kind="function",
        file_path=file_path,
        start_line=start,
        end_line=end,
        docstring=None,
        calls=(),
        parameters=(),
    )


def test_diff_touches_span_detection() -> None:
    # A unified diff modifying lines 15 to 25
    sample_diff = (
        "--- a/cache.py\n"
        "+++ b/cache.py\n"
        "@@ -15,10 +15,12 @@ def make_key():\n"
        "-    old_code\n"
        "+    new_code\n"
    )

    # Symbol at lines 10-30 intersects [15, 26] -> True
    assert SymbolChurnTracker._diff_touches_span(sample_diff, "cache.py", 10, 30) is True

    # Symbol at lines 1-10 does NOT intersect [15, 26] -> False
    assert SymbolChurnTracker._diff_touches_span(sample_diff, "cache.py", 1, 10) is False

    # Symbol at lines 50-70 does NOT intersect [15, 26] -> False
    assert SymbolChurnTracker._diff_touches_span(sample_diff, "cache.py", 50, 70) is False


def test_trace_symbol_finds_matching_commits(tmp_path: Path) -> None:
    sym = _make_sym("make_key", "cache.py", 10, 20)

    mock_history_reader = MagicMock()
    mock_history_reader.list_commits.return_value = [
        CommitRecord("c111", "Alice", "2026-10-01", "Update make_key"),
        CommitRecord("c222", "Bob", "2026-09-15", "Update other function"),
    ]

    mock_commit_reader = MagicMock()
    # c111 touches lines 10-20
    diff_c1 = "@@ -12,5 +12,6 @@\n+ new code\n"
    # c222 touches lines 80-90
    diff_c2 = "@@ -80,5 +80,5 @@\n- old code\n"

    def fake_read(commit_hash: str):
        diff = diff_c1 if commit_hash == "c111" else diff_c2
        return CommitEvidence(
            repo_root=str(tmp_path),
            commit_hash=commit_hash,
            author_name="Author",
            author_email="a@example.com",
            authored_at="2026-10-01",
            subject="Subj",
            body="Body",
            changed_files=(ChangedFile("cache.py", "M"),),
            diff=diff,
            diff_truncated=False,
        )

    mock_commit_reader.read_commit.side_effect = fake_read

    tracker = SymbolChurnTracker(
        repo_path=tmp_path,
        history_reader=mock_history_reader,
        commit_reader=mock_commit_reader,
    )

    hist = tracker.trace_symbol(sym)

    assert hist.churn_count == 1
    assert len(hist.commits) == 1
    assert hist.commits[0].commit_hash == "c111"
    assert hist.last_author == "Alice"


def test_rank_churn_orders_by_modification_frequency(tmp_path: Path) -> None:
    s_hot = _make_sym("frequent", "a.py", 1, 10)
    s_cold = _make_sym("rare", "b.py", 1, 10)

    tracker = SymbolChurnTracker(tmp_path)
    # Mock trace_symbol
    tracker.trace_symbol = MagicMock()
    tracker.trace_symbol.side_effect = lambda s, max_commits: MagicMock(
        symbol=s,
        churn_count=5 if s.name == "frequent" else 1,
    )

    ranked = tracker.rank_churn([s_cold, s_hot], top_n=2)
    assert len(ranked) == 2
    assert ranked[0].symbol.name == "frequent"
    assert ranked[1].symbol.name == "rare"
