from __future__ import annotations

from contextlib import AbstractAsyncContextManager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from randomtrust.repositories import (
    AuditRepository,
    EntropyRepository,
    RNGRepository,
    TestReportRepository,
)

class UnitOfWork(AbstractAsyncContextManager["UnitOfWork"]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self.session: AsyncSession | None = None

    async def __aenter__(self) -> "UnitOfWork":
        self.session = self._session_factory()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        assert self.session is not None
        if exc:
            await self.session.rollback()
        else:
            await self.session.commit()
        await self.session.close()

    @property
    def entropy(self) -> EntropyRepository:
        assert self.session is not None
        return EntropyRepository(self.session)

    @property
    def rng(self) -> RNGRepository:
        assert self.session is not None
        return RNGRepository(self.session)

    @property
    def audit(self) -> AuditRepository:
        assert self.session is not None
        return AuditRepository(self.session)

    @property
    def test_reports(self) -> TestReportRepository:
        assert self.session is not None
        return TestReportRepository(self.session)
