from __future__ import annotations

from typing import Iterable
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from randomtrust.analysis import AVAILABLE_TESTS
from randomtrust.api.dependencies import (
    get_analysis_service,
    get_unit_of_work,
)
from randomtrust.schemas.analysis import (
    AnalysisRequest,
    AuditAnalysisResponse,
    RunAnalysisResponse,
    TestOutcomeView,
)
from randomtrust.services import AnalysisService, UnitOfWork
from randomtrust.services.analysis_service import (
    SubjectDataUnavailableError,
    SubjectNotFoundError,
)

router = APIRouter()


@router.get("/tests", response_model=list[str])
async def list_available_tests() -> list[str]:
    return list(AVAILABLE_TESTS.keys())


def _serialize_outcomes(outcomes: Iterable) -> list[TestOutcomeView]:
    return [
        TestOutcomeView(
            name=outcome.name,
            passed=outcome.passed,
            statistic=float(outcome.metric),
            threshold=float(outcome.threshold),
            details={k: float(v) for k, v in outcome.details.items()},
        )
        for outcome in outcomes
    ]


@router.post("/runs/{run_id}", response_model=RunAnalysisResponse)
async def run_analysis_for_run(
    run_id: UUID,
    payload: AnalysisRequest,
    uow: UnitOfWork = Depends(get_unit_of_work),
    analysis_service: AnalysisService = Depends(get_analysis_service),
) -> RunAnalysisResponse:
    async with uow:
        try:
            result = await analysis_service.analyze_run(
                uow=uow,
                run_id=run_id,
                tests=payload.tests,
            )
        except SubjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except SubjectDataUnavailableError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    return RunAnalysisResponse(
        run_id=result.run_id,
        export_path=result.export_path,
        outcomes=_serialize_outcomes(result.outcomes),
    )


@router.post("/audits/{audit_id}", response_model=AuditAnalysisResponse)
async def run_analysis_for_audit(
    audit_id: UUID,
    payload: AnalysisRequest,
    uow: UnitOfWork = Depends(get_unit_of_work),
    analysis_service: AnalysisService = Depends(get_analysis_service),
) -> AuditAnalysisResponse:
    async with uow:
        try:
            result = await analysis_service.analyze_audit(
                uow=uow,
                audit_id=audit_id,
                tests=payload.tests,
            )
        except SubjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except SubjectDataUnavailableError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    return AuditAnalysisResponse(
        audit_id=result.audit_id,
        data_hash=result.data_hash,
        outcomes=_serialize_outcomes(result.outcomes),
    )
