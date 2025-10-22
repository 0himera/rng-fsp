from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from randomtrust.api.dependencies import get_rng_service, get_unit_of_work
from randomtrust.rng.generator import RNGOutputFormat
from randomtrust.schemas.rng import RNGGenerateRequest, RNGGenerateResponse
from randomtrust.services import RNGService, UnitOfWork

router = APIRouter()


@router.post("/generate", response_model=RNGGenerateResponse)
async def generate_rng(
    payload: RNGGenerateRequest,
    format: RNGOutputFormat = Query(default="hex"),
    uow: UnitOfWork = Depends(get_unit_of_work),
    rng_service: RNGService = Depends(get_rng_service),
) -> RNGGenerateResponse:
    overrides = payload.parameters.model_dump(exclude_none=True) if payload.parameters else None

    if payload.length <= 0 or payload.length > 1_000_000:
        raise HTTPException(status_code=422, detail="length must be between 1 and 1_000_000")

    async with uow:
        generated = await rng_service.generate(
            uow=uow,
            length=payload.length,
            fmt=format,
            noise_seed=payload.noise_seed,
            overrides=overrides,
        )

    return RNGGenerateResponse(
        run_id=generated.run_id,
        format=generated.format,
        data=generated.data,
        entropy_metrics=generated.metrics,
    )
