"""Autonomous multi-step investigation agent orchestrating tools and state transitions."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Callable

from whycode.agent.state import (
    EvidenceItem,
    InvestigationPlan,
    InvestigationReport,
    InvestigationState,
    SufficiencyAssessment,
)
from whycode.agent.tools import InvestigationToolbox
from whycode.llm.base import BaseLLM

logger = logging.getLogger(__name__)


def _extract_json_payload(raw_text: str) -> dict[str, Any]:
    """Safely extract and parse JSON object from LLM response text."""
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            if isinstance(data, dict):
                return data
        except Exception:
            pass

    return {}


class InvestigationAgent:
    """Stateful agent executing multi-hop repository investigations with reflection and guardrails."""

    def __init__(
        self,
        llm: BaseLLM,
        toolbox: InvestigationToolbox,
        max_iterations: int = 3,
        prompts_dir: Path | None = None,
    ) -> None:
        if max_iterations < 1:
            raise ValueError("max_iterations must be at least 1.")

        self.llm = llm
        self.toolbox = toolbox
        self.max_iterations = max_iterations
        self.prompts_dir = prompts_dir or (
            Path(__file__).resolve().parents[1] / "prompts"
        )

        self._plan_template = self._load_template("agent_plan.md")
        self._evaluate_template = self._load_template("agent_evaluate.md")
        self._synthesis_template = self._load_template("agent_synthesis.md")

    def _load_template(self, filename: str) -> str:
        template_file = self.prompts_dir / filename
        try:
            return template_file.read_text(encoding="utf-8")
        except OSError as exc:
            logger.warning("Could not read prompt template %s: %s", template_file, exc)
            return ""

    def investigate(
        self,
        query: str,
        on_step: Callable[[str, InvestigationState], None] | None = None,
    ) -> InvestigationReport:
        """Run an evidence-backed multi-step investigation loop."""
        state = InvestigationState(
            query=query.strip(),
            max_iterations=self.max_iterations,
        )

        # 1. Planning phase
        state.status = "planning"
        self._step_plan(state)
        if on_step:
            on_step("plan", state)

        # 2. Iterative tool execution & sufficiency reflection loop
        while not state.is_done:
            state.status = "executing_tools"
            self._step_execute_tools(state)
            if on_step:
                on_step("execute_tools", state)

            state.status = "evaluating"
            self._step_evaluate(state)
            state.iteration += 1
            if on_step:
                on_step("evaluate", state)

        # 3. Final synthesis phase
        state.status = "synthesizing"
        report = self._step_synthesize(state)
        state.report = report
        state.status = "completed"
        if on_step:
            on_step("synthesize", state)

        return report

    def _step_plan(self, state: InvestigationState) -> None:
        """Analyze query and formulate initial investigation roadmap."""
        repo_name = self.toolbox.repo_path.name
        rendered_prompt = self._plan_template.replace("{{ query }}", state.query).replace(
            "{{ repo_context }}", f"Repository: {repo_name} at {self.toolbox.repo_path}"
        )

        try:
            result = self.llm.generate(
                prompt=rendered_prompt,
                system="You are a precise software archaeology planner. Output valid JSON.",
            )
            data = _extract_json_payload(result.text)
        except Exception as exc:
            logger.warning("Agent planning prompt failed: %s", exc)
            data = {}

        hypotheses = data.get("hypotheses") or [f"Investigate implementation and rationale for '{state.query}'"]
        target_symbols = data.get("target_symbols") or []
        target_queries = data.get("target_queries") or [state.query]
        target_commits = data.get("target_commits") or []

        # If LLM didn't suggest symbols, extract candidate identifiers from query
        if not target_symbols:
            potential_symbols = re.findall(r"\b[A-Za-z_][A-Za-z0-9_]{2,}\b", state.query)
            target_symbols = [s for s in potential_symbols if s.lower() not in {"why", "what", "how", "when", "where", "the", "for", "and"}]

        state.plan = InvestigationPlan(
            hypotheses=hypotheses,
            target_symbols=target_symbols,
            target_queries=target_queries,
            target_commits=target_commits,
        )

    def _step_execute_tools(self, state: InvestigationState) -> None:
        """Execute diagnostic tools based on the current plan and evaluation feedback."""
        symbols_to_query: list[str] = []
        queries_to_run: list[str] = []
        commits_to_check: list[str] = []

        if state.iteration == 0 and state.plan is not None:
            symbols_to_query.extend(state.plan.target_symbols)
            queries_to_run.extend(state.plan.target_queries)
            commits_to_check.extend(state.plan.target_commits)
        elif state.sufficiency is not None:
            symbols_to_query.extend(state.sufficiency.next_target_symbols)
            queries_to_run.extend(state.sufficiency.next_target_queries)

        # 1. AST Symbol Inspection
        for sym in symbols_to_query:
            clean_sym = sym.strip()
            if clean_sym and clean_sym not in state.visited_symbols:
                state.record_symbol(clean_sym)
                item = self.toolbox.inspect_symbol(clean_sym)
                state.add_evidence(item)
                # Auto-harvest commits identified in churn for inspection
                for commit_str in re.findall(r"commit\s+([a-f0-9]{7,40})", item.content, re.IGNORECASE):
                    if commit_str not in state.visited_commits and commit_str not in commits_to_check:
                        commits_to_check.append(commit_str)

        # 2. Hybrid Code Retrieval
        for q in queries_to_run:
            clean_q = q.strip()
            if clean_q and clean_q not in state.visited_queries:
                state.record_query(clean_q)
                results = self.toolbox.search_code(clean_q, top_k=3)
                for res in results:
                    state.add_evidence(res)

        # 3. Git Commit Diff Inspection
        for c in commits_to_check:
            clean_c = c.strip()
            if clean_c and clean_c not in state.visited_commits:
                state.record_commit(clean_c)
                commit_item = self.toolbox.inspect_commit(clean_c)
                if commit_item is not None:
                    state.add_evidence(commit_item)

    def _step_evaluate(self, state: InvestigationState) -> None:
        """Reflect on accumulated evidence and determine if more hops are required."""
        # If iteration limit reached, short-circuit
        if state.iteration + 1 >= state.max_iterations:
            state.sufficiency = SufficiencyAssessment(
                is_sufficient=True,
                reasoning=f"Reached maximum iteration budget of {state.max_iterations} steps.",
            )
            return

        evidence_summaries = [f"[{e.kind.upper()}] {e.source}: {e.summary}" for e in state.evidence]
        rendered_prompt = (
            self._evaluate_template
            .replace("{{ query }}", state.query)
            .replace("{{ iteration }}", str(state.iteration + 1))
            .replace("{{ max_iterations }}", str(state.max_iterations))
            .replace("{{ hypotheses }}", "\n".join(f"- {h}" for h in (state.plan.hypotheses if state.plan else [])))
            .replace("{{ evidence_summary }}", "\n".join(evidence_summaries) if evidence_summaries else "No evidence collected yet.")
        )

        try:
            result = self.llm.generate(
                prompt=rendered_prompt,
                system="You are an evidence evaluation judge. Output valid JSON.",
            )
            data = _extract_json_payload(result.text)
        except Exception as exc:
            logger.warning("Agent evaluation prompt failed: %s", exc)
            data = {}

        is_sufficient = bool(data.get("is_sufficient", False))
        reasoning = data.get("reasoning", "Evidence evaluation completed.")
        remaining_questions = data.get("remaining_questions") or []
        next_symbols = data.get("next_target_symbols") or []
        next_queries = data.get("next_target_queries") or []

        # Guard against zero next-steps leading to infinite stagnation
        if not is_sufficient and not next_symbols and not next_queries:
            is_sufficient = True
            reasoning += " (No further targets identified; concluding investigation)."

        state.sufficiency = SufficiencyAssessment(
            is_sufficient=is_sufficient,
            reasoning=reasoning,
            remaining_questions=remaining_questions,
            next_target_symbols=next_symbols,
            next_target_queries=next_queries,
        )

    def _step_synthesize(self, state: InvestigationState) -> InvestigationReport:
        """Synthesize accumulated evidence into a grounded, comprehensive report."""
        evidence_blocks: list[str] = []
        citations: list[str] = []

        for idx, item in enumerate(state.evidence, start=1):
            citations.append(item.source)
            block = (
                f"### Evidence [{idx}]: {item.source} ({item.kind})\n"
                f"Summary: {item.summary}\n"
                f"```\n{item.content[:2000]}\n```"
            )
            evidence_blocks.append(block)

        evidence_str = "\n\n".join(evidence_blocks) if evidence_blocks else "No concrete evidence found."
        rendered_prompt = (
            self._synthesis_template
            .replace("{{ query }}", state.query)
            .replace("{{ evidence_items }}", evidence_str)
        )

        try:
            result = self.llm.generate(
                prompt=rendered_prompt,
                system="You are WhyCode. Synthesize a grounded software investigation report.",
            )
            raw_markdown = result.text.strip()
        except Exception as exc:
            logger.warning("Agent report synthesis failed: %s", exc)
            raw_markdown = f"## Investigation Report\n\nCould not synthesize report due to error: {exc}"

        # Extract structured sections from the markdown output
        summary = self._extract_section(raw_markdown, r"## Executive Summary\s*\n(.*?)(?=\n##|\Z)")
        timeline = self._extract_bullet_items(raw_markdown, r"## Historical Timeline & Commits\s*\n(.*?)(?=\n##|\Z)")
        root_causes = self._extract_bullet_items(raw_markdown, r"## Root Cause Analysis & Code Mechanism\s*\n(.*?)(?=\n##|\Z)")
        affected_symbols = self._extract_bullet_items(raw_markdown, r"## Impacted Callers & Architectural Scope\s*\n(.*?)(?=\n##|\Z)")
        uncertainties = self._extract_bullet_items(raw_markdown, r"## Uncertainties & Gaps\s*\n(.*?)(?=\n##|\Z)")

        if not summary:
            summary = raw_markdown[:300].strip()

        return InvestigationReport(
            query=state.query,
            summary=summary,
            timeline=timeline,
            root_causes=root_causes,
            affected_symbols=affected_symbols,
            citations=citations,
            uncertainties=uncertainties,
            raw_markdown=raw_markdown,
        )

    def _extract_section(self, text: str, pattern: str) -> str:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""

    def _extract_bullet_items(self, text: str, pattern: str) -> list[str]:
        section = self._extract_section(text, pattern)
        if not section:
            return []
        items: list[str] = []
        for line in section.splitlines():
            line_str = line.strip()
            if line_str.startswith(("- ", "* ", "1. ", "2. ", "3. ")):
                cleaned = re.sub(r"^[-*0-9.]+\s*", "", line_str).strip()
                if cleaned:
                    items.append(cleaned)
        return items
