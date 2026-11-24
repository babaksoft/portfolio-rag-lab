"""Correlation identifier handling for the HTTP boundary."""

import logging
from collections.abc import Awaitable, Callable
from time import perf_counter
from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse, Response

from portfolio_rag import (
    bind_correlation_id,
    current_correlation_id,
    reset_correlation_id,
)

CORRELATION_HEADER = "X-Correlation-ID"
MAX_CORRELATION_ID_LENGTH = 64
_NextHandler = Callable[[Request], Awaitable[Response]]
logger = logging.getLogger(__name__)


def get_correlation_id() -> str:
    """Return the correlation identifier for the active request context."""
    return current_correlation_id()


async def propagate_correlation_id(
    request: Request, call_next: _NextHandler
) -> Response:
    """Make one safe correlation identifier available across the request path."""
    correlation_id = _resolve_correlation_id(request)
    token = bind_correlation_id(correlation_id)
    started_at = perf_counter()

    try:
        try:
            response = await call_next(request)
        except Exception:
            logger.error(
                "request_failed",
                extra={
                    "event": "request_failed",
                    "correlation_id": correlation_id,
                    "error_code": "internal_error",
                    "outcome": "failure",
                },
            )
            response = JSONResponse(
                status_code=500,
                content={
                    "code": "internal_error",
                    "message": "The request could not be completed.",
                    "correlation_id": correlation_id,
                },
            )
    finally:
        reset_correlation_id(token)

    response.headers[CORRELATION_HEADER] = correlation_id
    logger.info(
        "request_completed",
        extra={
            "event": "request_completed",
            "correlation_id": correlation_id,
            "http_method": request.method,
            "http_path": _route_path(request),
            "http_status": response.status_code,
            "duration_ms": round((perf_counter() - started_at) * 1000, 2),
            "outcome": "success" if response.status_code < 400 else "failure",
        },
    )
    return response


def _resolve_correlation_id(request: Request) -> str:
    """Return a bounded incoming correlation identifier or create one."""
    candidate = request.headers.get(CORRELATION_HEADER, "").strip()
    if (
        candidate
        and len(candidate) <= MAX_CORRELATION_ID_LENGTH
        and candidate.isascii()
        and all(character.isalnum() or character in "._:-" for character in candidate)
    ):
        return candidate

    return str(uuid4())


def _route_path(request: Request) -> str:
    """Return the trusted route template without logging attacker-chosen paths."""
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    return path if isinstance(path, str) else "unmatched"
