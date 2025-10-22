from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence
from uuid import UUID

from minio import Minio
from minio.error import S3Error

from randomtrust.analysis import TestOutcome, run_selected_tests
from randomtrust.core import Settings

from .unit_of_work import UnitOfWork


class AnalysisError(RuntimeError):
    """Базовая ошибка анализа."""


class SubjectNotFoundError(AnalysisError):
    """Запрашиваемый объект не найден."""


class SubjectDataUnavailableError(AnalysisError):
    """У объекта отсутствуют данные для анализа."""


@dataclass(slots=True)
class RunAnalysisResult:
    run_id: UUID
    export_path: str
    outcomes: Sequence[TestOutcome]


@dataclass(slots=True)
class AuditAnalysisResult:
    audit_id: UUID
    data_hash: str
    outcomes: Sequence[TestOutcome]


class AnalysisService:
    def __init__(
        self,
        *,
        storage: Minio,
        settings: Settings,
    ) -> None:
        self._storage = storage
        self._settings = settings

    async def analyze_run(
        self,
        *,
        uow: UnitOfWork,
        run_id: UUID,
        tests: Iterable[str] | None = None,
    ) -> RunAnalysisResult:
        run = await uow.rng.get_run(run_id)
        if run is None:
            raise SubjectNotFoundError(f"run {run_id} not found")
        if not run.export_path:
            raise SubjectDataUnavailableError("run has no persisted payload")

        payload = self._download_bytes(run.export_path)
        bits = self._bytes_to_bits(payload)
        outcomes = run_selected_tests(bits, tests)

        await uow.test_reports.delete_for_run(run_id)
        for outcome in outcomes:
            metrics = self._build_metrics_payload(outcome)
            status = "passed" if outcome.passed else "failed"
            await uow.test_reports.add_report(
                run_id=run_id,
                test_name=outcome.name,
                status=status,
                metrics=metrics,
                report_path=None,
            )

        return RunAnalysisResult(run_id=run_id, export_path=run.export_path, outcomes=outcomes)

    async def analyze_audit(
        self,
        *,
        uow: UnitOfWork,
        audit_id: UUID,
        tests: Iterable[str] | None = None,
    ) -> AuditAnalysisResult:
        audit = await uow.audit.get_upload(audit_id)
        if audit is None:
            raise SubjectNotFoundError(f"audit upload {audit_id} not found")

        bits = self._bytes_to_bits(audit.raw_payload)
        outcomes = run_selected_tests(bits, tests)
        return AuditAnalysisResult(audit_id=audit_id, data_hash=audit.data_hash, outcomes=outcomes)

    def _download_bytes(self, path: str) -> bytes:
        obj = None
        try:
            obj = self._storage.get_object(self._settings.minio_bucket, path)
            data = obj.read()
        except S3Error as exc:
            raise SubjectDataUnavailableError(f"failed to fetch object {path}: {exc}") from exc
        finally:
            if obj is not None:
                try:
                    obj.close()
                    obj.release_conn()
                except Exception:
                    pass
        return data

    @staticmethod
    def _bytes_to_bits(payload: bytes) -> list[int]:
        bits: list[int] = []
        for byte in payload:
            for shift in range(7, -1, -1):
                bits.append((byte >> shift) & 1)
        return bits

    @staticmethod
    def _build_metrics_payload(outcome: TestOutcome) -> dict[str, float]:
        metrics: dict[str, float] = {
            "statistic": float(outcome.metric),
            "threshold": float(outcome.threshold),
        }
        for key, value in outcome.details.items():
            metrics[key] = float(value)
        return metrics
