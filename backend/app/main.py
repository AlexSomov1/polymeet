from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from app.api.errors import register_error_handlers
from app.api.health import router as health_router
from app.api.openapi import API_DESCRIPTION, OPENAPI_TAGS, install_openapi, operation_id
from app.api.v1.router import api_router
from app.core.config import Settings, get_settings
from app.core.db import create_engine, create_session_factory
from app.core.logging import configure_logging
from app.core.metrics import setup_metrics
from app.core.middleware import RequestContextMiddleware
from app.core.redis import create_redis

logger = structlog.get_logger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_engine(settings.database_url)
        redis = create_redis(settings.redis_url)
        app.state.engine = engine
        app.state.session_factory = create_session_factory(engine)
        app.state.redis = redis
        logger.info("app_started", env=settings.app_env)
        try:
            yield
        finally:
            await redis.aclose()
            await engine.dispose()
            logger.info("app_stopped")

    app = FastAPI(
        title="PolyMeet API",
        version="0.1.0",
        description=API_DESCRIPTION,
        openapi_tags=OPENAPI_TAGS,
        # Документация под /api, как в README: nginx проксирует на API весь /api/
        docs_url="/api/docs",
        swagger_ui_oauth2_redirect_url="/api/docs/oauth2-redirect",
        redoc_url=None,
        openapi_url="/api/openapi.json",
        generate_unique_id_function=operation_id,
        lifespan=lifespan,
    )
    app.state.settings = settings

    register_error_handlers(app)
    app.include_router(health_router)
    app.include_router(api_router)
    install_openapi(app)
    setup_metrics(app)
    # Добавляется последним, чтобы быть внешним: видит итоговый статус и любое исключение.
    app.add_middleware(RequestContextMiddleware)
    return app


app = create_app()
