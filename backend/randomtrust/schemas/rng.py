from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from .entropy import NoiseParameters


class RNGGenerateRequest(BaseModel):
    length: int = Field(..., ge=1, le=1_000_000)
    noise_seed: int | None = Field(default=None, ge=0)
    parameters: NoiseParameters | None = None


class RNGGenerateResponse(BaseModel):
    run_id: UUID
    format: str
    data: str | list[int]
    entropy_metrics: dict[str, float]
