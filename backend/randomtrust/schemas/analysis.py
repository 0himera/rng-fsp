from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    tests: list[str] | None = Field(default=None, description="Optional subset of tests to execute")


class TestOutcomeView(BaseModel):
    name: str
    passed: bool
    statistic: float
    threshold: float
    details: dict[str, float]


class RunAnalysisResponse(BaseModel):
    run_id: UUID
    export_path: str
    outcomes: list[TestOutcomeView]


class AuditAnalysisResponse(BaseModel):
    audit_id: UUID
    data_hash: str
    outcomes: list[TestOutcomeView]
