from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class AuditSequenceRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    description: str | None = Field(default=None, max_length=1_024)
    data: str = Field(..., description="Hex-encoded sequence to audit")


class AuditSequenceResponse(BaseModel):
    audit_id: UUID
    status: str
