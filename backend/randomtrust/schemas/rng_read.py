from __future__ import annotations

from uuid import UUID

from datetime import datetime

from pydantic import BaseModel, Field


class TestReportView(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    test_name: str
    status: str
    metrics: dict[str, float]
    report_path: str | None


class RNGRunSummary(BaseModel):
    id: UUID
    entropy_simulation_id: UUID | None
    run_format: str = Field(..., max_length=16)
    length: int
    entropy_metrics: dict[str, float]
    seed_hash: str
    export_path: str | None
    created_at: datetime
    updated_at: datetime


class RNGRunDetail(RNGRunSummary):
    run_checksum: str | None = Field(default=None, description="Hex-encoded checksum")
    test_reports: list[TestReportView]
