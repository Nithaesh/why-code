from whycode.agent.state import (
    EvidenceItem,
    InvestigationPlan,
    InvestigationReport,
    InvestigationState,
    SufficiencyAssessment,
)


def test_evidence_item_creation():
    item = EvidenceItem(
        kind="code_chunk",
        source="src/whycode/cache.py:10-25",
        summary="Cache lookup logic",
        content="def get(key): ...",
        metadata={"score": 0.95},
    )
    assert item.kind == "code_chunk"
    assert item.source == "src/whycode/cache.py:10-25"
    assert item.metadata["score"] == 0.95


def test_investigation_state_deduplication():
    state = InvestigationState(query="Why does cache expire?", max_iterations=3)

    item1 = EvidenceItem(
        kind="code_chunk",
        source="src/whycode/cache.py:10-25",
        summary="Cache lookup logic",
        content="def get(key): ...",
    )
    item2 = EvidenceItem(
        kind="code_chunk",
        source="src/whycode/cache.py:10-25",
        summary="Duplicate entry",
        content="def get(key): ...",
    )
    item3 = EvidenceItem(
        kind="symbol_graph",
        source="symbol:DiskCache",
        summary="DiskCache definition",
        content="class DiskCache: ...",
    )

    assert state.add_evidence(item1) is True
    assert len(state.evidence) == 1

    # Adding identical kind and source returns False (no duplicate)
    assert state.add_evidence(item2) is False
    assert len(state.evidence) == 1

    # Adding distinct item succeeds
    assert state.add_evidence(item3) is True
    assert len(state.evidence) == 2


def test_investigation_state_is_done_guardrail():
    state = InvestigationState(query="Test query", max_iterations=2)
    assert state.is_done is False

    # Still not done at iteration 1
    state.iteration = 1
    assert state.is_done is False

    # Done when reaching max_iterations
    state.iteration = 2
    assert state.is_done is True


def test_investigation_state_is_done_sufficiency():
    state = InvestigationState(query="Test query", max_iterations=5)
    assert state.is_done is False

    state.sufficiency = SufficiencyAssessment(
        is_sufficient=False,
        reasoning="More data needed",
    )
    assert state.is_done is False

    state.sufficiency = SufficiencyAssessment(
        is_sufficient=True,
        reasoning="Root cause conclusively identified",
    )
    assert state.is_done is True


def test_investigation_state_tracking():
    state = InvestigationState(query="Test query")
    state.record_symbol("DiskCache")
    state.record_commit("a1b2c3d")
    state.record_query("cache expiration")

    assert "DiskCache" in state.visited_symbols
    assert "a1b2c3d" in state.visited_commits
    assert "cache expiration" in state.visited_queries
