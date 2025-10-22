from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Request

from randomtrust.core import (
    Settings,
    create_engine,
    create_minio_client,
    create_session_factory,
    get_settings,
)
from randomtrust.entropy import EntropyMixer, LorenzChaosSimulator, NoiseSimulator
from randomtrust.rng.generator import ChaCha20RNGFactory
from randomtrust.services import AuditService, EntropyService, RNGService, UnitOfWork


@lru_cache
def _noise_simulator() -> NoiseSimulator:
    return NoiseSimulator()


@lru_cache
def _chaos_simulator() -> LorenzChaosSimulator:
    return LorenzChaosSimulator()


def get_settings_dep() -> Settings:
    return get_settings()


def get_noise_simulator() -> NoiseSimulator:
    return _noise_simulator()


def get_chaos_simulator() -> LorenzChaosSimulator:
    return _chaos_simulator()


def get_entropy_mixer(
    noise_simulator: Annotated[NoiseSimulator, Depends(get_noise_simulator)],
    chaos_simulator: Annotated[LorenzChaosSimulator, Depends(get_chaos_simulator)],
) -> EntropyMixer:
    return EntropyMixer(noise_simulator=noise_simulator, chaos_simulator=chaos_simulator)


def get_rng_factory(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings_dep)],
) -> ChaCha20RNGFactory:
    redis_client = getattr(request.app.state, "redis_client", None)
    if redis_client is None:
        raise RuntimeError("Redis client is not initialized")
    return ChaCha20RNGFactory(redis_client=redis_client, namespace=f"rng_runs:{settings.environment}")


def get_session_factory(request: Request, settings: Annotated[Settings, Depends(get_settings_dep)]):
    session_factory = getattr(request.app.state, "session_factory", None)
    if session_factory is None:
        engine = create_engine(settings)
        session_factory = create_session_factory(engine)
        request.app.state.engine = engine
        request.app.state.session_factory = session_factory
    return session_factory


def get_unit_of_work(
    session_factory=Depends(get_session_factory),
) -> UnitOfWork:
    return UnitOfWork(session_factory=session_factory)


def get_minio_client(request: Request, settings: Annotated[Settings, Depends(get_settings_dep)]):
    client = getattr(request.app.state, "minio_client", None)
    if client is None:
        client = create_minio_client(settings)
        request.app.state.minio_client = client
    return client


def get_entropy_service(
    mixer: Annotated[EntropyMixer, Depends(get_entropy_mixer)],
    settings: Annotated[Settings, Depends(get_settings_dep)],
    minio = Depends(get_minio_client),
) -> EntropyService:
    return EntropyService(mixer=mixer, storage=minio, settings=settings)


def get_rng_service(
    entropy_service: Annotated[EntropyService, Depends(get_entropy_service)],
    rng_factory: Annotated[ChaCha20RNGFactory, Depends(get_rng_factory)],
    settings: Annotated[Settings, Depends(get_settings_dep)],
    minio = Depends(get_minio_client),
) -> RNGService:
    return RNGService(
        entropy_service=entropy_service,
        rng_factory=rng_factory,
        storage=minio,
        settings=settings,
    )


def get_audit_service(
    settings: Annotated[Settings, Depends(get_settings_dep)],
    minio = Depends(get_minio_client),
) -> AuditService:
    return AuditService(storage=minio, settings=settings)
