from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class NoiseParameters(BaseModel):
    duration_ms: int | None = Field(default=None, ge=50, le=1_000)
    hum_amplitude: float | None = Field(default=None, ge=0.0, le=1.0)
    noise_amplitude: float | None = Field(default=None, ge=0.0, le=1.0)
    spike_density: float | None = Field(default=None, ge=0.0, le=0.2)
    spike_amplitude: float | None = Field(default=None, ge=0.0, le=1.0)


class EntropyMixRequest(BaseModel):
    noise_seed: int | None = Field(default=None, ge=0)
    parameters: NoiseParameters | None = None


class EntropyMetrics(BaseModel):
    snr_db: float = Field(...)
    spectral_deviation_percent: float = Field(...)
    lyapunov_exponent: float = Field(...)


class EntropyMixResponse(BaseModel):
    simulation_id: UUID
    seed_hex: str
    metrics: EntropyMetrics
