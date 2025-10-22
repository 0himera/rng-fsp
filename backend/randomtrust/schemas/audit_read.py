from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AuditUploadSummary(BaseModel):
    id: UUID
    name: str
    description: str | None
    data_hash: str
    created_at: datetime
    updated_at: datetime


class AuditUploadDetail(AuditUploadSummary):
    result_path: str | None
