from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from randomtrust.api.dependencies import (
    get_entropy_service,
    get_unit_of_work,
)
from randomtrust.schemas.entropy import EntropyMixRequest, EntropyMixResponse, EntropyMetrics
from randomtrust.schemas.entropy_read import (
    ChaosRunInfo,
    EntropySimulationDetail,
    EntropySimulationSummary,
)
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


def _serialize_chaos_run(chaos_run) -> ChaosRunInfo:
    return ChaosRunInfo(
        id=chaos_run.id,
        created_at=chaos_run.created_at,
        updated_at=chaos_run.updated_at,
        config=chaos_run.config,
        lyapunov_exponent=chaos_run.lyapunov_exponent,
        trajectory_checksum=chaos_run.trajectory_checksum,
    )


def _serialize_simulation_summary(simulation) -> EntropySimulationSummary:
    return EntropySimulationSummary(
        id=simulation.id,
        created_at=simulation.created_at,
        updated_at=simulation.updated_at,
        noise_seed=simulation.noise_seed,
        metrics=simulation.metrics,
        seed_hex=simulation.seed_hex,
    )


def _serialize_simulation_detail(simulation) -> EntropySimulationDetail:
    chaos = _serialize_chaos_run(simulation.chaos_run) if simulation.chaos_run else None
    return EntropySimulationDetail(
        **_serialize_simulation_summary(simulation).model_dump(),
        noise_config=simulation.noise_config,
        pool_hash=simulation.pool_hash.hex(),
        chaos_checksum=simulation.chaos_checksum,
        noise_raw_path=simulation.noise_raw_path,
        chaos_raw_path=simulation.chaos_raw_path,
        chaos_run=chaos,
    )


@router.get("/simulations", response_model=list[EntropySimulationSummary])
async def list_simulations(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> list[EntropySimulationSummary]:
    async with uow:
        records = await uow.entropy.list_simulations(limit=limit, offset=offset)
    return [_serialize_simulation_summary(record) for record in records]


@router.get("/simulations/{simulation_id}", response_model=EntropySimulationDetail)
async def get_simulation(
    simulation_id: UUID,
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> EntropySimulationDetail:
    async with uow:
        record = await uow.entropy.get_simulation(simulation_id)
    if record is None:
        raise HTTPException(status_code=404, detail="simulation not found")
    return _serialize_simulation_detail(record)
