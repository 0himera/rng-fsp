from __future__ import annotations

import uuid

from sqlalchemy import LargeBinary, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class AuditUpload(TimestampMixin, Base):
    __tablename__ = "audit_uploads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    data_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    result_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    raw_payload: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
