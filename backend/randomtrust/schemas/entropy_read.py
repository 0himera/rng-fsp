from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ChaosRunInfo(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    config: dict[str, Any]
    lyapunov_exponent: float
    trajectory_checksum: str


class EntropySimulationSummary(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    noise_seed: int | None
    metrics: dict[str, float]
    seed_hex: str


class EntropySimulationDetail(EntropySimulationSummary):
    noise_config: dict[str, Any]
    pool_hash: str = Field(description="Hex-encoded pool hash")
    chaos_checksum: str
    noise_raw_path: str
    chaos_raw_path: str
    chaos_run: ChaosRunInfo | None
