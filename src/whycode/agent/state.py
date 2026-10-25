"""Data models and state representations for the agentic investigation workflow."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


EvidenceKind = Literal["code_chunk", "symbol_graph", "commit", "churn"]


@dataclass(frozen=True, slots=True)
class EvidenceItem:
    """An atomic, grounded piece of evidence collected by an agent tool."""

    kind: EvidenceKind
    source: str
    summary: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class InvestigationPlan:
    """The agent's structured roadmap of hypotheses and inquiry targets."""

    hypotheses: list[str] = field(default_factory=list)
    target_symbols: list[str] = field(default_factory=list)
    target_queries: list[str] = field(default_factory=list)
    target_commits: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SufficiencyAssessment:
    """Evaluation of whether gathered evidence sufficiently answers the investigation query."""

    is_sufficient: bool
    reasoning: str
    remaining_questions: list[str] = field(default_factory=list)
    next_target_symbols: list[str] = field(default_factory=list)
    next_target_queries: list[str] = field(default_factory=list)


@dataclass(slots=True)
class InvestigationReport:
    """Final synthesized findings of an agentic investigation."""

    query: str
    summary: str
    timeline: list[str] = field(default_factory=list)
    root_causes: list[str] = field(default_factory=list)
    affected_symbols: list[str] = field(default_factory=list)
    citations: list[str] = field(default_factory=list)
    uncertainties: list[str] = field(default_factory=list)
    raw_markdown: str = ""


@dataclass(slots=True)
class InvestigationState:
    """Stateful ledger tracking the progression of an agentic investigation."""

    query: str
    max_iterations: int = 3
    iteration: int = 0
    status: str = "initialized"
    plan: InvestigationPlan | None = None
    evidence: list[EvidenceItem] = field(default_factory=list)
    visited_symbols: set[str] = field(default_factory=set)
    visited_commits: set[str] = field(default_factory=set)
    visited_queries: set[str] = field(default_factory=set)
    sufficiency: SufficiencyAssessment | None = None
    report: InvestigationReport | None = None

    @property
    def is_done(self) -> bool:
        """Return True if the investigation has concluded or reached its iteration budget."""
        if self.sufficiency is not None and self.sufficiency.is_sufficient:
            return True
        return self.iteration >= self.max_iterations

    def add_evidence(self, item: EvidenceItem) -> bool:
        """Add an evidence item if its (kind, source) signature is not already recorded."""
        for existing in self.evidence:
            if existing.kind == item.kind and existing.source == item.source:
                return False
        self.evidence.append(item)
        return True

    def record_symbol(self, symbol_name: str) -> None:
        self.visited_symbols.add(symbol_name)

    def record_commit(self, commit_hash: str) -> None:
        self.visited_commits.add(commit_hash)

    def record_query(self, query: str) -> None:
        self.visited_queries.add(query)
