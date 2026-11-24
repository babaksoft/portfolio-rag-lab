"""Safe structured logging shared by process adapters."""

import json
import logging
from contextvars import ContextVar, Token
from datetime import UTC, datetime
from typing import Any

_STANDARD_RECORD_FIELDS = frozenset(logging.makeLogRecord({}).__dict__)
_SAFE_CONTEXT_FIELDS = frozenset(
    {
        "correlation_id",
        "duration_ms",
        "error_code",
        "event",
        "http_method",
        "http_path",
        "http_status",
        "outcome",
        "service",
    }
)
_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="unknown")


def bind_correlation_id(value: str) -> Token[str]:
    """Bind a correlation identifier to the current execution context."""
    return _correlation_id.set(value)


def current_correlation_id() -> str:
    """Return the correlation identifier bound to the current context."""
    return _correlation_id.get()


def reset_correlation_id(token: Token[str]) -> None:
    """Restore the correlation context represented by a previous token."""
    _correlation_id.reset(token)


class JsonLogFormatter(logging.Formatter):
    """Serialize a bounded set of operational fields as one JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        """Return a JSON log line without exception or request payload details."""
        fields: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "event": getattr(record, "event", "unclassified_log"),
        }
        for name in _SAFE_CONTEXT_FIELDS:
            if name in _STANDARD_RECORD_FIELDS or name == "event":
                continue
            value = getattr(record, name, None)
            if value is not None:
                fields[name] = value
        return json.dumps(fields, separators=(",", ":"), sort_keys=True)


def configure_structured_logging(*, service: str, level: str = "INFO") -> None:
    """Configure the root logger for safe container-standard-output logs.

    Args:
        service:
            Stable process identity attached to every subsequently emitted record.
        level:
            Standard Python logging level name.
    """
    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())
    handler.addFilter(_ServiceFilter(service))

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)


class _ServiceFilter(logging.Filter):
    """Attach the configured process identity to every root-handler record."""

    def __init__(self, service: str) -> None:
        super().__init__()
        self._service = service

    def filter(self, record: logging.LogRecord) -> bool:
        record.service = self._service
        if not hasattr(record, "correlation_id"):
            correlation_id = current_correlation_id()
            if correlation_id != "unknown":
                record.correlation_id = correlation_id
        return True
