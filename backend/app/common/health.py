from typing import Literal

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app import __version__
from app.common.responses import APIResponse, error_response, success_response
from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.core.runtime import RuntimeState
from app.database.session import ping_database

logger = get_logger(__name__)

router = APIRouter(tags=["Health"])

CheckStatus = Literal["ok", "error"]
ProbeStatus = Literal["ok", "unavailable"]


class ProbeCheck(BaseModel):
    status: CheckStatus
    detail: str | None = None


class LivenessData(BaseModel):
    status: Literal["ok"] = "ok"
    version: str = __version__


class ReadinessData(BaseModel):
    status: ProbeStatus
    checks: dict[str, ProbeCheck] = Field(default_factory=dict)


def _settings(request: Request) -> Settings:
    stored = getattr(request.app.state, "settings", None)
    return stored if isinstance(stored, Settings) else get_settings()


def _runtime(request: Request) -> RuntimeState | None:
    runtime = getattr(request.app.state, "runtime", None)
    return runtime if isinstance(runtime, RuntimeState) else None


@router.get(
    "/health",
    summary="Liveness probe",
    description="Process is running. Orchestrators use this to decide whether to restart the pod.",
    response_model=APIResponse[LivenessData],
)
async def liveness() -> APIResponse[LivenessData]:
    return success_response(LivenessData())


@router.get(
    "/ready",
    summary="Readiness probe",
    description="Accepts traffic only when startup finished, the process is not draining, "
    "and the database answers SELECT 1.",
    response_model=APIResponse[ReadinessData],
    responses={503: {"model": APIResponse[ReadinessData]}},
)
async def readiness(request: Request) -> JSONResponse:
    settings = _settings(request)
    runtime = _runtime(request)
    checks: dict[str, ProbeCheck] = {"app": ProbeCheck(status="ok")}

    if runtime is None or not runtime.ready or runtime.shutting_down:
        checks["app"] = ProbeCheck(status="error", detail="Application is not ready")
        return _ready_response(checks, available=False)

    if settings.READY_CHECK_DATABASE:
        try:
            await ping_database()
            checks["database"] = ProbeCheck(status="ok")
        except Exception as exc:
            logger.warning("readiness_database_failed", error=str(exc))
            checks["database"] = ProbeCheck(status="error", detail="Database unreachable")
            return _ready_response(checks, available=False)
    else:
        checks["database"] = ProbeCheck(status="ok", detail="skipped")

    return _ready_response(checks, available=True)


def _ready_response(checks: dict[str, ProbeCheck], *, available: bool) -> JSONResponse:
    data = ReadinessData(status="ok" if available else "unavailable", checks=checks)
    if available:
        payload = success_response(data, message="Ready")
        return JSONResponse(status_code=200, content=payload.model_dump())
    error = error_response("Service unavailable")
    body = error.model_dump()
    body["data"] = data.model_dump()
    return JSONResponse(status_code=503, content=body)
