"""Process health routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from portfolio_rag.api.dependencies import get_api_settings
from portfolio_rag.api.models import HealthResponse
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
    settings: Annotated[ApiSettings, Depends(get_api_settings)],
) -> HealthResponse:
    """Report readiness while the process has no external dependencies."""
    return HealthResponse(status="ok", service=settings.service_name)
