from __future__ import annotations

import io
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from randomtrust.api.dependencies import get_rng_service, get_unit_of_work
from randomtrust.rng.generator import RNGOutputFormat
from randomtrust.schemas.rng import RNGGenerateRequest, RNGGenerateResponse
from randomtrust.schemas.rng_read import RNGRunDetail, RNGRunSummary, TestReportView
from randomtrust.services import RNGService, UnitOfWork
from randomtrust.services.rng_service import (
    InsufficientBitsError,
    RunDataUnavailableError,
    RunNotFoundError,
)

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


def _serialize_run_summary(record) -> RNGRunSummary:
    return RNGRunSummary(
        id=record.id,
        entropy_simulation_id=record.entropy_simulation_id,
        run_format=record.run_format,
        length=record.length,
        entropy_metrics=record.entropy_metrics,
        seed_hash=record.seed_hash,
        export_path=record.export_path,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _serialize_test_report(report) -> TestReportView:
    return TestReportView(
        id=report.id,
        created_at=report.created_at,
        updated_at=report.updated_at,
        test_name=report.test_name,
        status=report.status,
        metrics=report.metrics,
        report_path=report.report_path,
    )


def _serialize_run_detail(record) -> RNGRunDetail:
    checksum = record.run_checksum.hex() if record.run_checksum else None
    return RNGRunDetail(
        **_serialize_run_summary(record).model_dump(),
        run_checksum=checksum,
        test_reports=[_serialize_test_report(r) for r in record.test_reports],
    )


@router.get("/runs", response_model=list[RNGRunSummary])
async def list_runs(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> list[RNGRunSummary]:
    async with uow:
        records = await uow.rng.list_runs(limit=limit, offset=offset)
    return [_serialize_run_summary(record) for record in records]


@router.get("/runs/{run_id}", response_model=RNGRunDetail)
async def get_run(
    run_id: UUID,
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> RNGRunDetail:
    async with uow:
        record = await uow.rng.get_run(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="run not found")
    return _serialize_run_detail(record)


@router.get("/runs/{run_id}/export", response_class=StreamingResponse)
async def export_run_bits(
    run_id: UUID,
    min_bits: int = Query(default=1_000_000, ge=1, description="Minimum number of bits required"),
    uow: UnitOfWork = Depends(get_unit_of_work),
    rng_service: RNGService = Depends(get_rng_service),
):
    async with uow:
        try:
            export = await rng_service.export_bits(uow=uow, run_id=run_id, min_bits=min_bits)
        except RunNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except RunDataUnavailableError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except InsufficientBitsError as exc:
            detail = {
                "error": str(exc),
                "available_bits": exc.available,
                "required_bits": exc.required,
            }
            raise HTTPException(status_code=422, detail=detail) from exc

    headers = {"Content-Disposition": f'attachment; filename="{export.filename}"'}
    stream = io.BytesIO(export.content)
    return StreamingResponse(stream, media_type="text/plain", headers=headers)
