"""Safe HTTP error translation for the API boundary."""

from fastapi import Request
from fastapi.responses import JSONResponse

from portfolio_rag.api.correlation import get_correlation_id
from portfolio_rag.api.models import ErrorResponse


async def handle_validation_error(request: Request, exc: Exception) -> JSONResponse:
    """Translate validation details into a stable user-safe response."""
    del request, exc
    error = ErrorResponse(
        code="invalid_request",
        message="The request payload is invalid.",
        correlation_id=get_correlation_id(),
    )
    return JSONResponse(status_code=422, content=error.model_dump(mode="json"))
