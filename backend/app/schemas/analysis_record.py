from datetime import datetime
from typing import Annotated, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, JsonValue, StringConstraints, model_validator

NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100_000)]
JobTitle = Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)]
Version = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ScoreBreakdown(Contract):
    required_skills: int = Field(ge=0, le=60, strict=True)
    preferred_skills: int = Field(ge=0, le=20, strict=True)
    evidence_quality: int = Field(ge=0, le=20, strict=True)



class EvidenceItem(Contract):
    source: str
    category: str
    label: str
    line: int | None = Field(default=None, ge=1, strict=True)
    text: str
class MatchResult(Contract):
    score: int = Field(ge=0, le=100, strict=True)
    score_breakdown: ScoreBreakdown
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    resume_sections: dict[str, JsonValue] = Field(default_factory=dict)
    job_skills: list[JsonValue] = Field(default_factory=list)
    suggestions: list[JsonValue] = Field(default_factory=list)
    evidence_items: list[EvidenceItem] = Field(default_factory=list)
    confirmed_skills: list[str] = Field(default_factory=list)
    confirmed_name: str | None = Field(default=None, max_length=200)
    algorithm_version: Version

    @model_validator(mode="after")
    def check_total(self) -> Self:
        if self.score != sum(self.score_breakdown.model_dump().values()):
            raise ValueError("score must equal the sum of score_breakdown")
        return self


class RecordCreate(Contract):
    resume_text: NonEmptyText
    jd_text: NonEmptyText
    job_title: JobTitle | None = None
    result: MatchResult


class RecordUpdate(Contract):
    # Only metadata changes: analysis inputs/results are immutable snapshots.
    job_title: JobTitle | None


class RecordSummary(Contract):
    id: UUID
    job_title: str | None
    score: int
    algorithm_version: str
    created_at: datetime


class RecordDetail(MatchResult):
    id: UUID
    job_title: str | None
    resume_text: str
    jd_text: str
    created_at: datetime


class RecordPage(Contract):
    items: list[RecordSummary]
    total: int
    limit: int
    offset: int
