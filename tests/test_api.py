from pathlib import Path
from typing import Any
from fastapi.testclient import TestClient

from whycode.__main__ import build_parser
from whycode.api.app import create_app
from whycode.llm.base import BaseLLM, LLMResult


class FakeLLM(BaseLLM):
    def __init__(self, response: str = "Test answer.") -> None:
        self.response = response
        self.call_count = 0

    def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        system: str | None = None,
        temperature: float = 0.0,
        response_schema: dict[str, Any] | None = None,
    ) -> LLMResult:
        self.call_count += 1
        return LLMResult(text=self.response)


class ScriptedLLM(BaseLLM):
    def __init__(self, responses: list[str]) -> None:
        self.responses = list(responses)
        self.call_count = 0

    def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        system: str | None = None,
        temperature: float = 0.0,
        response_schema: dict[str, Any] | None = None,
    ) -> LLMResult:
        self.call_count += 1
        text = self.responses.pop(0) if self.responses else "{}"
        return LLMResult(text=text)


def setup_sample_repo(tmp_path: Path):
    (tmp_path / "auth.py").write_text(
        "def authenticate(token):\n    '''Verify credential token.'''\n    return token == 'secret'\n",
        encoding="utf-8",
    )
    (tmp_path / "server.py").write_text(
        "from auth import authenticate\n\ndef login(req):\n    return authenticate(req.token)\n",
        encoding="utf-8",
    )


def test_api_health_endpoint(tmp_path: Path):
    setup_sample_repo(tmp_path)
    app = create_app(repo_path=tmp_path)
    client = TestClient(app)

    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"
    assert str(tmp_path) in data["repo_path"]


def test_api_search_endpoint(tmp_path: Path):
    setup_sample_repo(tmp_path)
    app = create_app(repo_path=tmp_path)
    client = TestClient(app)

    response = client.post(
        "/api/v1/search",
        json={"query": "authenticate", "top_k": 3, "mode": "lexical"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "authenticate"
    assert data["total_results"] >= 1
    first = data["results"][0]
    assert "auth.py" in first["file_path"]
    assert "authenticate" in first["content"]


def test_api_symbol_and_churn_endpoints(tmp_path: Path):
    setup_sample_repo(tmp_path)
    app = create_app(repo_path=tmp_path)
    client = TestClient(app)

    # 1. Symbol inspection
    sym_resp = client.get("/api/v1/symbol/authenticate")
    assert sym_resp.status_code == 200
    sym_data = sym_resp.json()
    assert sym_data["query"] == "authenticate"
    assert len(sym_data["definitions"]) >= 1
    assert sym_data["definitions"][0]["file_path"] == "auth.py"
    assert any(c["name"] == "login" for c in sym_data["callers"])

    # 2. Churn hotspots
    churn_resp = client.get("/api/v1/churn?limit=5")
    assert churn_resp.status_code == 200
    churn_data = churn_resp.json()
    assert "hotspots" in churn_data


def test_api_ask_endpoint(tmp_path: Path):
    setup_sample_repo(tmp_path)
    fake_llm = FakeLLM("The authenticate function compares token with secret [Source 1].")
    app = create_app(repo_path=tmp_path, llm=fake_llm)
    client = TestClient(app)

    response = client.post(
        "/api/v1/ask",
        json={"question": "How does authenticate work?", "top_k": 3, "mode": "lexical"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["question"] == "How does authenticate work?"
    assert "authenticate function" in data["answer"]
    assert len(data["sources"]) >= 1
    assert data["sources"][0]["file_path"] in ("auth.py", "server.py")


def test_api_investigate_endpoint(tmp_path: Path):
    setup_sample_repo(tmp_path)

    plan_json = """
    {
      "hypotheses": ["Auth logic refactored"],
      "target_symbols": ["authenticate"],
      "target_queries": ["authenticate"],
      "target_commits": []
    }
    """
    eval_json = """
    {
      "is_sufficient": true,
      "reasoning": "Found direct definition and callers",
      "remaining_questions": [],
      "next_target_symbols": [],
      "next_target_queries": []
    }
    """
    synth_md = """
    ## Executive Summary
    Authentication is performed via token equality in auth.py.

    ## Historical Timeline & Commits
    - 2026-10-25: Created authentication logic.

    ## Root Cause Analysis & Code Mechanism
    - Token compared with secret string.

    ## Impacted Callers & Architectural Scope
    - login in server.py

    ## Evidence Citations
    - auth.py:1-3

    ## Uncertainties & Gaps
    - None.
    """

    scripted_llm = ScriptedLLM([plan_json, eval_json, synth_md])
    app = create_app(repo_path=tmp_path, llm=scripted_llm)
    client = TestClient(app)

    response = client.post(
        "/api/v1/investigate",
        json={"query": "Investigate authentication implementation", "max_steps": 2},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "Investigate authentication implementation"
    assert "token equality in auth.py" in data["summary"]
    assert "login in server.py" in data["affected_symbols"]
    assert len(data["citations"]) >= 1


def test_api_validation_errors(tmp_path: Path):
    app = create_app(repo_path=tmp_path)
    client = TestClient(app)

    # Empty search query -> 422 Unprocessable Entity
    resp = client.post("/api/v1/search", json={"query": "", "top_k": 5})
    assert resp.status_code == 422

    # Invalid top_k (exceeds max 50) -> 422
    resp = client.post("/api/v1/search", json={"query": "test", "top_k": 999})
    assert resp.status_code == 422


def test_cli_serve_parser():
    parser = build_parser()
    args = parser.parse_args(["serve", "/my/repo", "--host", "0.0.0.0", "--port", "9000"])
    assert args.command == "serve"
    assert args.repo == "/my/repo"
    assert args.host == "0.0.0.0"
    assert args.port == 9000
