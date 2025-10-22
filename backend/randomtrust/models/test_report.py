from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class TestReport(TimestampMixin, Base):
    __tablename__ = "test_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rng_runs.id", ondelete="CASCADE"), nullable=False
    )
    test_name: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    metrics: Mapped[dict[str, float]] = mapped_column(JSON, nullable=False)
    report_path: Mapped[str | None] = mapped_column(String(512), nullable=True)

    rng_run = relationship("RNGRun", back_populates="test_reports")
