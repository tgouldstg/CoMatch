from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class CompanyRecord(BaseModel):
    id: str = Field(..., description="Unique record identifier")
    name: str = Field(..., description="Company name")
    website: str | None = Field(default=None, description="Optional website/domain")
    country: str | None = Field(default=None, description="Optional country code/name")
    metadata: dict[str, Any] | None = Field(default=None, description="Arbitrary extra fields")


class MatchOptions(BaseModel):
    top_k: int = Field(default=3, ge=1, le=10)
    auto_accept_threshold: float = Field(default=0.92, ge=0.0, le=1.0)
    review_threshold: float = Field(default=0.75, ge=0.0, le=1.0)
    include_alternatives: bool = True


class MatchRequest(BaseModel):
    left: list[CompanyRecord]
    right: list[CompanyRecord]
    options: MatchOptions = MatchOptions()


class MatchCandidate(BaseModel):
    id: str
    name: str
    confidence: float
    score_breakdown: dict[str, float]


class MatchResult(BaseModel):
    left_id: str
    left_name: str
    best_match: MatchCandidate | None
    alternatives: list[MatchCandidate] = []
    decision: Literal["auto_accept", "review", "reject"]


class MatchResponse(BaseModel):
    results: list[MatchResult]
    summary: dict[str, int]
