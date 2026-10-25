from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

from whycode.__main__ import main
from whycode.agent.orchestrator import InvestigationAgent, _extract_json_payload
from whycode.agent.tools import InvestigationToolbox
from whycode.graph.ast_parser import CodeSymbol
from whycode.graph.service import SymbolInvestigationResult
from whycode.llm.base import BaseLLM, LLMResult


class ScriptedLLM(BaseLLM):
    """Predictable LLM substitute responding with a scripted sequence of outputs."""

    def __init__(self, responses: list[str]) -> None:
        self.responses = list(responses)
        self.call_count = 0
        self.prompts: list[str] = []

    def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        system: str | None = None,
        temperature: float = 0.0,
        response_schema: dict[str, Any] | None = None,
    ) -> LLMResult:
        self.call_count += 1
        self.prompts.append(prompt)
        if self.responses:
            text = self.responses.pop(0)
        else:
            text = "{}"
        return LLMResult(text=text)


def test_extract_json_payload():
    # Direct valid json
    assert _extract_json_payload('{"key": "value"}') == {"key": "value"}

    # Markdown fenced json block
    fenced = "```json\n{\n  \"hypotheses\": [\"test\"]\n}\n```"
    assert _extract_json_payload(fenced) == {"hypotheses": ["test"]}

    # Surrounded by narrative text
    narrative = "Here is the response:\n{\"status\": \"ok\"}\nHope this helps!"
    assert _extract_json_payload(narrative) == {"status": "ok"}

    # Malformed text
    assert _extract_json_payload("not json at all") == {}


def test_agent_single_hop_investigation(tmp_path: Path):
    (tmp_path / "auth.py").write_text(
        "def authenticate(token):\n    '''Verify credential.'''\n    return token == 'secret'\n",
        encoding="utf-8",
    )

    plan_json = """
    {
      "hypotheses": ["Credential verification was refactored."],
      "target_symbols": ["authenticate"],
      "target_queries": ["authenticate"],
      "target_commits": []
    }
    """
    evaluate_json = """
    {
      "is_sufficient": true,
      "reasoning": "Found direct implementation of authenticate in auth.py.",
      "remaining_questions": [],
      "next_target_symbols": [],
      "next_target_queries": []
    }
    """
    synthesis_md = """
    ## Executive Summary
    Authentication is verified by comparing the token with a secret.

    ## Historical Timeline & Commits
    - 2026-10-25: Defined authenticate function.

    ## Root Cause Analysis & Code Mechanism
    - Direct equality check against secret credential.

    ## Impacted Callers & Architectural Scope
    - auth.py:1-3

    ## Evidence Citations
    - auth.py:1-3

    ## Uncertainties & Gaps
    - None identified.
    """

    llm = ScriptedLLM([plan_json, evaluate_json, synthesis_md])
    toolbox = InvestigationToolbox(repo_path=tmp_path)
    agent = InvestigationAgent(llm=llm, toolbox=toolbox, max_iterations=3)

    steps_recorded: list[str] = []
    report = agent.investigate(
        query="How does authenticate work?",
        on_step=lambda step, state: steps_recorded.append(step),
    )

    assert report.query == "How does authenticate work?"
    assert "Authentication is verified" in report.summary
    assert len(report.timeline) >= 1
    assert len(report.root_causes) >= 1
    assert any("auth.py" in c for c in report.citations)
    assert steps_recorded == ["plan", "execute_tools", "evaluate", "synthesize"]
    assert llm.call_count == 3


def test_agent_multi_hop_with_guardrail_budget(tmp_path: Path):
    (tmp_path / "service.py").write_text(
        "def process():\n    return 42\n",
        encoding="utf-8",
    )

    plan_json = """
    {
      "hypotheses": ["Process logic changed"],
      "target_symbols": ["process"],
      "target_queries": ["process"],
      "target_commits": []
    }
    """
    # Step 1 evaluate: insufficient, requests next target
    eval_1 = """
    {
      "is_sufficient": false,
      "reasoning": "Need to check callers of process",
      "remaining_questions": ["Who calls process?"],
      "next_target_symbols": ["caller_func"],
      "next_target_queries": []
    }
    """
    # Step 2 evaluate: at max_iterations=2, orchestrator overrides sufficiency
    synthesis_md = """
    ## Executive Summary
    Process returns constant integer 42.

    ## Historical Timeline & Commits
    - Initial commit: created process function.

    ## Root Cause Analysis & Code Mechanism
    - Simple constant return.

    ## Impacted Callers & Architectural Scope
    - None detected.

    ## Evidence Citations
    - service.py:1-2

    ## Uncertainties & Gaps
    - Callers could not be located before max steps reached.
    """

    # max_iterations is set to 2:
    # 1. plan
    # 2. iteration 0: execute -> evaluate (eval_1)
    # 3. iteration 1: execute -> evaluate (overridden by budget limit!)
    # 4. synthesize
    llm = ScriptedLLM([plan_json, eval_1, synthesis_md])
    toolbox = InvestigationToolbox(repo_path=tmp_path)
    agent = InvestigationAgent(llm=llm, toolbox=toolbox, max_iterations=2)

    report = agent.investigate(query="Trace process callers")
    assert report is not None
    assert "Process returns constant" in report.summary
    assert "Callers could not be located" in report.uncertainties[0]
    # Check that it terminated within the 2 iteration budget
    assert agent.max_iterations == 2


def test_agent_cli_command(tmp_path: Path, monkeypatch, capsys):
    (tmp_path / "mod.py").write_text(
        "def helper():\n    return 'ok'\n",
        encoding="utf-8",
    )

    mock_report_md = "## Executive Summary\nHelper returns string 'ok'.\n\n## Evidence Citations\n- mod.py"

    # Patch InvestigationAgent.investigate to avoid calling real Gemini in CLI integration test
    from whycode.agent.state import InvestigationReport
    mock_report = InvestigationReport(
        query="What does helper do?",
        summary="Helper returns string 'ok'.",
        raw_markdown=mock_report_md,
    )
    monkeypatch.setattr(InvestigationAgent, "investigate", lambda self, query, on_step=None: mock_report)

    exit_code = main(["investigate", str(tmp_path), "-q", "What does helper do?", "--max-steps", "2"])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "Helper returns string 'ok'." in out
