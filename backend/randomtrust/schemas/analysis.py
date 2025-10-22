from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from randomtrust.analysis import AVAILABLE_TESTS


class AnalysisRequest(BaseModel):
    tests: list[str] | None = Field(default=None, description="Optional subset of tests to execute")

    @field_validator("tests")
    @classmethod
    def validate_tests(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        unknown = sorted({name for name in value if name not in AVAILABLE_TESTS})
        if unknown:
            raise ValueError(f"unknown tests requested: {', '.join(unknown)}")
        return value


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
