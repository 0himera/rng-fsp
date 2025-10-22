from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from randomtrust.models import AuditUpload


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_upload(
        self,
        *,
        audit_id: uuid.UUID,
        name: str,
        description: str | None,
        data_hash: str,
        result_path: str | None,
        raw_payload: bytes,
    ) -> AuditUpload:
        record = AuditUpload(
            id=audit_id,
            name=name,
            description=description,
            data_hash=data_hash,
            result_path=result_path,
            raw_payload=raw_payload,
        )
        self._session.add(record)
        return record

    async def get_upload(self, audit_id: uuid.UUID) -> AuditUpload | None:
        stmt = select(AuditUpload).where(AuditUpload.id == audit_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
