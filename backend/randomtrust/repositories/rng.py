from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from randomtrust.models import RNGRun


class RNGRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_run(
        self,
        *,
        run_id: uuid.UUID,
        entropy_simulation_id: uuid.UUID | None,
        run_format: str,
        length: int,
        entropy_metrics: dict[str, float],
        seed_hash: str,
        export_path: str | None,
        run_checksum: bytes | None,
    ) -> RNGRun:
        record = RNGRun(
            id=run_id,
            entropy_simulation_id=entropy_simulation_id,
            run_format=run_format,
            length=length,
            entropy_metrics=entropy_metrics,
            seed_hash=seed_hash,
            export_path=export_path,
            run_checksum=run_checksum,
        )
        self._session.add(record)
        return record

    async def get_run(self, run_id: uuid.UUID) -> RNGRun | None:
        stmt = select(RNGRun).options(selectinload(RNGRun.test_reports)).where(RNGRun.id == run_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_runs(self, *, limit: int, offset: int) -> list[RNGRun]:
        stmt = (
            select(RNGRun)
            .order_by(RNGRun.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars())
