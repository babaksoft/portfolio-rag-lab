"""Process health routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from portfolio_rag.api.dependencies import get_api_settings, get_readiness_probe
from portfolio_rag.api.models import HealthResponse
from portfolio_rag.api.readiness import ReadinessProbe
from portfolio_rag.api.settings import ApiSettings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", response_model=HealthResponse)
async def liveness(
    settings: Annotated[ApiSettings, Depends(get_api_settings)],
) -> HealthResponse:
    """Report process liveness without checking dependencies."""
    return HealthResponse(status="ok", service=settings.service_name)


@router.get("/ready", response_model=HealthResponse)
async def readiness(
    response: Response,
    settings: Annotated[ApiSettings, Depends(get_api_settings)],
    probe: Annotated[ReadinessProbe, Depends(get_readiness_probe)],
) -> HealthResponse:
    """Report whether all dependencies required for traffic are available."""
    if not await probe.is_ready():
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(status="unavailable", service=settings.service_name)

    return HealthResponse(status="ok", service=settings.service_name)
