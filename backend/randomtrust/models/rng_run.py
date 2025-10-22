from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, JSON, LargeBinary, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class RNGRun(TimestampMixin, Base):
    __tablename__ = "rng_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entropy_simulation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entropy_simulations.id", ondelete="SET NULL"), nullable=True
    )
    run_format: Mapped[str] = mapped_column(String(16), nullable=False)
    length: Mapped[int] = mapped_column(Integer, nullable=False)
    entropy_metrics: Mapped[dict[str, float]] = mapped_column(JSON, nullable=False)
    seed_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    export_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    run_checksum: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)

    entropy_simulation = relationship("EntropySimulation")
    test_reports = relationship("TestReport", back_populates="rng_run", cascade="all, delete-orphan")
