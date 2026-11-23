"""Safe HTTP error translation for the API boundary."""

from fastapi import Request
from fastapi.responses import JSONResponse

from portfolio_rag.api.correlation import get_correlation_id
from portfolio_rag.api.models import ErrorResponse


class AccessDeniedError(Exception):
    """Represent a safe authentication or authorization failure."""

    def __init__(self, *, status_code: int, code: str, message: str) -> None:
        """Initialize the bounded HTTP error representation."""
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


async def handle_validation_error(request: Request, exc: Exception) -> JSONResponse:
    """Translate validation details into a stable user-safe response."""
    del request, exc

    error = ErrorResponse(
        code="invalid_request",
        message="The request payload is invalid.",
        correlation_id=get_correlation_id(),
    )
    return JSONResponse(status_code=422, content=error.model_dump(mode="json"))


async def handle_access_denied(request: Request, exc: Exception) -> JSONResponse:
    """Translate access failures without exposing credential diagnostics."""
    del request
    if not isinstance(exc, AccessDeniedError):
        raise TypeError("handle_access_denied received an unexpected exception")

    error = ErrorResponse(
        code=exc.code,
        message=exc.message,
        correlation_id=get_correlation_id(),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error.model_dump(mode="json"),
    )
