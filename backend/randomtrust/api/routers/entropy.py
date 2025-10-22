from uuid import UUID

from fastapi import APIRouter, Depends

from randomtrust.api.dependencies import (
    get_entropy_service,
    get_unit_of_work,
)
from randomtrust.schemas.entropy import EntropyMixRequest, EntropyMixResponse, EntropyMetrics
from randomtrust.services import EntropyService, UnitOfWork

router = APIRouter()


@router.post("/mix", response_model=EntropyMixResponse)
async def mix_entropy(
    payload: EntropyMixRequest,
    uow: UnitOfWork = Depends(get_unit_of_work),
    entropy_service: EntropyService = Depends(get_entropy_service),
) -> EntropyMixResponse:
    overrides = payload.parameters.model_dump(exclude_none=True) if payload.parameters else None
    async with uow:
        stored = await entropy_service.create_entropy(
            uow=uow,
            noise_seed=payload.noise_seed,
            overrides=overrides,
        )

    metrics = EntropyMetrics(
        snr_db=stored.metrics["snr_db"],
        spectral_deviation_percent=stored.metrics["spectral_deviation_percent"],
        lyapunov_exponent=stored.metrics["lyapunov_exponent"],
    )

    return EntropyMixResponse(
        simulation_id=stored.simulation_id,
        seed_hex=stored.seed_hex,
        metrics=metrics,
    )
