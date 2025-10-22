from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import ForeignKey, JSON, LargeBinary, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class EntropySimulation(TimestampMixin, Base):
    __tablename__ = "entropy_simulations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    noise_seed: Mapped[int | None] = mapped_column(nullable=True)
    noise_config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    metrics: Mapped[dict[str, float]] = mapped_column(JSON, nullable=False)
    seed_hex: Mapped[str] = mapped_column(String(128), nullable=False)
    pool_hash: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    chaos_checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    noise_raw_path: Mapped[str] = mapped_column(String(512), nullable=False)
    chaos_raw_path: Mapped[str] = mapped_column(String(512), nullable=False)

    chaos_run: Mapped["ChaosRun"] = relationship(back_populates="entropy_simulation", uselist=False)


class ChaosRun(TimestampMixin, Base):
    __tablename__ = "chaos_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    simulation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entropy_simulations.id", ondelete="CASCADE"), nullable=False
    )
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    lyapunov_exponent: Mapped[float]
    trajectory_checksum: Mapped[str] = mapped_column(String(128), nullable=False)

    entropy_simulation: Mapped[EntropySimulation] = relationship(back_populates="chaos_run")
