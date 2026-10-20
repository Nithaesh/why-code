
import json

import pytest

from whycode.git.reader import ChangedFile, CommitEvidence
from whycode.llm.base import BaseLLM, LLMResult
from whycode.summarizer import (
    CommitSummaryError,
    CommitSummaryService,
)


class FakeLLM(BaseLLM):
    def __init__(self, response: str) -> None:
        self.response = response
        self.last_prompt = ""
        self.last_system = None
        self.last_schema = None
        self.last_temperature = None

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.0,
        response_schema: dict | None = None,
    ) -> LLMResult:
        self.last_prompt = prompt
        self.last_system = system
        self.last_schema = response_schema
        self.last_temperature = temperature
        return LLMResult(text=self.response)


@pytest.fixture
def evidence() -> CommitEvidence:
    return CommitEvidence(
        repo_root="C:/fake-repo",
        commit_hash="abc123",
        author_name="Test Author",
        author_email="test@example.com",
        authored_at="2026-10-16T12:00:00+00:00",
        subject="Add greeting function",
        body="",
        changed_files=(
            ChangedFile(path="hello.py", status="A"),
        ),
        diff='+def greet():\n+    return "hello"\n',
        diff_truncated=False,
    )


def valid_response() -> str:
    return json.dumps({
        "summary": "Adds a greeting function.",
        "changes": [
            "Defines greet() in hello.py.",
            'Returns the string "hello".',
        ],
        "likely_purpose": "To provide a simple greeting function.",
        "evidence": [
            {
                "file": "hello.py",
                "detail": "The diff adds greet() and its return statement.",
            }
        ],
        "uncertainties": [
            "The diff does not establish where the function will be used."
        ],
    })


def test_returns_validated_summary(evidence: CommitEvidence) -> None:
    llm = FakeLLM(valid_response())
    service = CommitSummaryService(llm)

    result = service.summarize(evidence)

    assert result.summary == "Adds a greeting function."
    assert result.evidence[0].file == "hello.py"
    assert llm.last_temperature == 0.0
    assert llm.last_schema is not None
    assert "Add greeting function" in llm.last_prompt
    assert "return" in llm.last_prompt


def test_rejects_invalid_json(evidence: CommitEvidence) -> None:
    service = CommitSummaryService(FakeLLM("not valid JSON"))

    with pytest.raises(CommitSummaryError, match="failed validation"):
        service.summarize(evidence)


def test_rejects_evidence_for_unchanged_file(
    evidence: CommitEvidence,
) -> None:
    response = json.loads(valid_response())
    response["evidence"][0]["file"] = "secret.py"

    service = CommitSummaryService(FakeLLM(json.dumps(response)))

    with pytest.raises(CommitSummaryError, match="not changed"):
        service.summarize(evidence)


def test_rejects_unexpected_fields(evidence: CommitEvidence) -> None:
    response = json.loads(valid_response())
    response["made_up_field"] = "unexpected"

    service = CommitSummaryService(FakeLLM(json.dumps(response)))

    with pytest.raises(CommitSummaryError, match="failed validation"):
        service.summarize(evidence)


def test_truncated_diff_is_disclosed_to_llm(
    evidence: CommitEvidence,
) -> None:
    truncated_evidence = CommitEvidence(
        repo_root=evidence.repo_root,
        commit_hash=evidence.commit_hash,
        author_name=evidence.author_name,
        author_email=evidence.author_email,
        authored_at=evidence.authored_at,
        subject=evidence.subject,
        body=evidence.body,
        changed_files=evidence.changed_files,
        diff=evidence.diff,
        diff_truncated=True,
    )

    llm = FakeLLM(valid_response())
    service = CommitSummaryService(llm)

    service.summarize(truncated_evidence)

    payload_start = llm.last_prompt.index("{")
    payload = json.loads(llm.last_prompt[payload_start:])

    assert payload["diff_truncated"] is True
    assert "truncated diff" in llm.last_system.lower()
    assert "complete change" in llm.last_system.lower()


def test_rejects_empty_evidence_without_uncertainty(
    evidence: CommitEvidence,
) -> None:
    response = json.loads(valid_response())
    response["evidence"] = []
    response["uncertainties"] = []

    service = CommitSummaryService(FakeLLM(json.dumps(response)))

    with pytest.raises(CommitSummaryError):
        service.summarize(evidence)
