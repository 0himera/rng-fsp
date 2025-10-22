from __future__ import annotations

import io
import uuid
from hashlib import blake2s

from minio import Minio

from randomtrust.core import Settings

from .unit_of_work import UnitOfWork


class AuditRecord:
    def __init__(
        self,
        *,
        audit_id: uuid.UUID,
        status: str,
        data_hash: str,
    ) -> None:
        self.audit_id = audit_id
        self.status = status
        self.data_hash = data_hash


class AuditService:
    def __init__(self, *, storage: Minio, settings: Settings) -> None:
        self._storage = storage
        self._settings = settings

    async def store_sequence(
        self,
        *,
        uow: UnitOfWork,
        name: str,
        description: str | None,
        hex_payload: str,
    ) -> AuditRecord:
        payload = bytes.fromhex(hex_payload)
        audit_id = uuid.uuid4()

        path = f"audit/{audit_id}.bin"
        stream = io.BytesIO(payload)
        self._storage.put_object(
            self._settings.minio_bucket,
            path,
            data=stream,
            length=len(payload),
            content_type="application/octet-stream",
        )

        data_hash = blake2s(payload).hexdigest()

        repo = uow.audit
        await repo.add_upload(
            audit_id=audit_id,
            name=name,
            description=description,
            data_hash=data_hash,
            result_path=path,
            raw_payload=payload,
        )

        return AuditRecord(audit_id=audit_id, status="stored", data_hash=data_hash)
