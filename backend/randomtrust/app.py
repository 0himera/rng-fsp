from contextlib import asynccontextmanager

from fastapi import FastAPI

from randomtrust.api import api_router
from randomtrust.core import (
    Settings,
    close_redis,
    create_engine,
    create_minio_client,
    create_redis,
    create_session_factory,
    dispose_engine,
    get_settings,
    setup_logging,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    settings = get_settings()
    redis_client = create_redis(settings)
    engine = create_engine(settings)
    session_factory = create_session_factory(engine)
    minio_client = create_minio_client(settings)

    app.state.redis_client = redis_client
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.minio_client = minio_client

    try:
        yield
    finally:
        if redis_client is not None:
            await close_redis(redis_client)
        if engine is not None:
            await dispose_engine(engine)


def create_app() -> FastAPI:
    settings: Settings = get_settings()
    app = FastAPI(  # noqa: F841
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )

    app.include_router(api_router, prefix=settings.api_prefix)

    return app
