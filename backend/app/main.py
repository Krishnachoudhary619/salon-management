from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.appointments.router import router as appointments_router
from app.auth.router import router as auth_router
from app.billing.router import invoices_router, payments_router
from app.commissions.router import router as commissions_router
from app.common.health import router as health_router
from app.core.config import get_settings
from app.core.constants import REQUEST_ID_HEADER, RETRY_AFTER_HEADER
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.middleware import (
    HostHeaderMiddleware,
    RateLimitMiddleware,
    RequestContextMiddleware,
    SecurityHeadersMiddleware,
    ShutdownDrainMiddleware,
)
from app.core.runtime import RuntimeState
from app.customers.router import router as customers_router
from app.dashboard.router import router as dashboard_router
from app.database.session import engine, wait_for_database
from app.performance.router import router as performance_router
from app.public.router import router as public_router
from app.schedules.router import availability_router
from app.schedules.router import router as schedules_router
from app.services.router import router as services_router
from app.staff.router import router as staff_router
from app.tasks.router import router as tasks_router
from app.tips.router import router as tips_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    runtime: RuntimeState = application.state.runtime
    logger.info("application_starting", env=settings.APP_ENV, version=__version__)
    if settings.WAIT_FOR_DATABASE:
        await wait_for_database(settings)
    runtime.mark_ready()
    logger.info("application_ready")
    try:
        yield
    finally:
        logger.info("application_stopping")
        await runtime.begin_shutdown(settings.GRACEFUL_SHUTDOWN_SECONDS)
        await engine.dispose()
        logger.info("application_stopped")


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)

    application = FastAPI(
        title=settings.APP_NAME,
        version=__version__,
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url="/redoc" if settings.docs_enabled else None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
        lifespan=lifespan,
    )
    application.state.settings = settings
    application.state.runtime = RuntimeState()
    if not settings.WAIT_FOR_DATABASE:
        application.state.runtime.mark_ready()

    register_exception_handlers(application)
    # Last add_middleware is outermost. CORS must wrap Trusted Host.
    application.add_middleware(RequestContextMiddleware)
    application.add_middleware(SecurityHeadersMiddleware)
    application.add_middleware(RateLimitMiddleware)
    application.add_middleware(ShutdownDrainMiddleware)
    application.add_middleware(HostHeaderMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=settings.cors_origin_list != ["*"],
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", REQUEST_ID_HEADER],
        expose_headers=[REQUEST_ID_HEADER, RETRY_AFTER_HEADER, "X-RateLimit-Remaining"],
        max_age=600,
    )

    application.include_router(health_router)
    application.include_router(auth_router, prefix=settings.API_V1_PREFIX)
    application.include_router(staff_router, prefix=settings.API_V1_PREFIX)
    application.include_router(services_router, prefix=settings.API_V1_PREFIX)
    application.include_router(customers_router, prefix=settings.API_V1_PREFIX)
    application.include_router(schedules_router, prefix=settings.API_V1_PREFIX)
    application.include_router(availability_router, prefix=settings.API_V1_PREFIX)
    application.include_router(appointments_router, prefix=settings.API_V1_PREFIX)
    application.include_router(payments_router, prefix=settings.API_V1_PREFIX)
    application.include_router(invoices_router, prefix=settings.API_V1_PREFIX)
    application.include_router(commissions_router, prefix=settings.API_V1_PREFIX)
    application.include_router(tips_router, prefix=settings.API_V1_PREFIX)
    application.include_router(tasks_router, prefix=settings.API_V1_PREFIX)
    application.include_router(dashboard_router, prefix=settings.API_V1_PREFIX)
    application.include_router(performance_router, prefix=settings.API_V1_PREFIX)
    application.include_router(public_router, prefix=settings.API_V1_PREFIX)
    return application


app = create_app()
