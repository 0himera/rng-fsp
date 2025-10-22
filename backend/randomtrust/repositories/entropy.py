from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from randomtrust.models import ChaosRun, EntropySimulation


class EntropyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_simulation(
        self,
        *,
        simulation_id: uuid.UUID,
        noise_seed: int | None,
        noise_config: dict,
        metrics: dict[str, float],
        seed_hex: str,
        pool_hash: bytes,
        chaos_checksum: str,
        noise_raw_path: str,
        chaos_raw_path: str,
    ) -> EntropySimulation:
        simulation = EntropySimulation(
            id=simulation_id,
            noise_seed=noise_seed,
            noise_config=noise_config,
            metrics=metrics,
            seed_hex=seed_hex,
            pool_hash=pool_hash,
            chaos_checksum=chaos_checksum,
            noise_raw_path=noise_raw_path,
            chaos_raw_path=chaos_raw_path,
        )
        self._session.add(simulation)
        return simulation

    async def add_chaos_run(
        self,
        *,
        simulation_id: uuid.UUID,
        config: dict,
        lyapunov_exponent: float,
        trajectory_checksum: str,
    ) -> ChaosRun:
        record = ChaosRun(
            simulation_id=simulation_id,
            config=config,
            lyapunov_exponent=lyapunov_exponent,
            trajectory_checksum=trajectory_checksum,
        )
        self._session.add(record)
        return record

    async def get_simulation(self, simulation_id: uuid.UUID) -> EntropySimulation | None:
        stmt = (
            select(EntropySimulation)
            .options(selectinload(EntropySimulation.chaos_run))
            .where(EntropySimulation.id == simulation_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_simulations(self, *, limit: int, offset: int) -> list[EntropySimulation]:
        stmt = (
            select(EntropySimulation)
            .options(selectinload(EntropySimulation.chaos_run))
            .order_by(EntropySimulation.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars())
