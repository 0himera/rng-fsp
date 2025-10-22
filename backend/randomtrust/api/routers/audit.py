from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from randomtrust.api.dependencies import get_audit_service, get_unit_of_work
from randomtrust.schemas.audit import AuditSequenceRequest, AuditSequenceResponse
from randomtrust.services import AuditService, UnitOfWork

router = APIRouter()


@router.post("/upload", response_model=AuditSequenceResponse)
async def upload_sequence(
    payload: AuditSequenceRequest,
    uow: UnitOfWork = Depends(get_unit_of_work),
    audit_service: AuditService = Depends(get_audit_service),
) -> AuditSequenceResponse:
    try:
        bytes.fromhex(payload.data)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="data must be hex-encoded") from exc

    async with uow:
        record = await audit_service.store_sequence(
            uow=uow,
            name=payload.name,
            description=payload.description,
            hex_payload=payload.data,
        )

    return AuditSequenceResponse(audit_id=record.audit_id, status=record.status)
