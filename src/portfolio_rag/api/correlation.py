"""Correlation identifier handling for the HTTP boundary."""

from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from uuid import uuid4

from fastapi import Request
from fastapi.responses import Response

CORRELATION_HEADER = "X-Correlation-ID"
MAX_CORRELATION_ID_LENGTH = 64
_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="unknown")
_NextHandler = Callable[[Request], Awaitable[Response]]


def get_correlation_id() -> str:
    """Return the correlation identifier for the active request context."""
    return _correlation_id.get()


async def propagate_correlation_id(
    request: Request, call_next: _NextHandler
) -> Response:
    """Make one safe correlation identifier available across the request path."""
    correlation_id = _resolve_correlation_id(request)
    token = _correlation_id.set(correlation_id)

    try:
        response = await call_next(request)
    finally:
        _correlation_id.reset(token)

    response.headers[CORRELATION_HEADER] = correlation_id
    return response


def _resolve_correlation_id(request: Request) -> str:
    """Return a bounded incoming correlation identifier or create one."""
    candidate = request.headers.get(CORRELATION_HEADER, "").strip()
    if (
        candidate
        and len(candidate) <= MAX_CORRELATION_ID_LENGTH
        and candidate.isascii()
        and candidate.isprintable()
    ):
        return candidate

    return str(uuid4())
