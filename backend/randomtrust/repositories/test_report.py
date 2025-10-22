from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from randomtrust.models import TestReport


class TestReportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_report(
        self,
        *,
        run_id: str,
        test_name: str,
        status: str,
        metrics: dict[str, float],
        report_path: str | None,
    ) -> TestReport:
        record = TestReport(
            run_id=run_id,
            test_name=test_name,
            status=status,
            metrics=metrics,
            report_path=report_path,
        )
        self._session.add(record)
        return record

    async def list_by_run(self, run_id: str) -> list[TestReport]:
        stmt = select(TestReport).where(TestReport.run_id == run_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
