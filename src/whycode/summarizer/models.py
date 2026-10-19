
from pydantic import BaseModel, ConfigDict, Field


class EvidenceItem(BaseModel):
    """A claim tied to a file changed by the commit."""

    model_config = ConfigDict(extra="forbid")

    file: str = Field(description="Exact path of a changed file")
    detail: str = Field(
        description="What the diff directly shows in this file"
    )


class CommitSummary(BaseModel):
    """Structured explanation of a Git commit."""

    model_config = ConfigDict(extra="forbid")

    summary: str = Field(
        description="A concise, factual summary of the commit"
    )
    changes: list[str] = Field(
        description="Specific changes directly supported by the diff"
    )
    likely_purpose: str = Field(
        description="The likely goal, clearly qualified if uncertain"
    )
    evidence: list[EvidenceItem] = Field(
        description="File-level evidence supporting the explanation"
    )
    uncertainties: list[str] = Field(
        description="What cannot be established from the available evidence"
    )
