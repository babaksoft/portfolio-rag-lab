import json
import logging

from portfolio_rag import JsonLogFormatter


def test_json_log_formatter_emits_only_bounded_operational_fields() -> None:
    record = logging.LogRecord(
        name="portfolio_rag.test",
        level=logging.ERROR,
        pathname=__file__,
        lineno=1,
        msg="secret raw content",
        args=(),
        exc_info=None,
    )
    record.event = "request_failed"
    record.service = "portfolio-rag-api"
    record.correlation_id = "safe-correlation"
    record.error_code = "internal_error"
    record.identity_assertion = "credential-must-not-appear"

    result = json.loads(JsonLogFormatter().format(record))

    assert result["event"] == "request_failed"
    assert result["service"] == "portfolio-rag-api"
    assert result["correlation_id"] == "safe-correlation"
    assert result["error_code"] == "internal_error"
    assert "secret raw content" not in json.dumps(result)
    assert "credential-must-not-appear" not in json.dumps(result)


def test_json_log_formatter_bounds_unclassified_library_logs() -> None:
    record = logging.LogRecord(
        name="third_party",
        level=logging.WARNING,
        pathname=__file__,
        lineno=1,
        msg="possibly sensitive library diagnostic",
        args=(),
        exc_info=None,
    )

    result = json.loads(JsonLogFormatter().format(record))

    assert result["event"] == "unclassified_log"
    assert "possibly sensitive" not in json.dumps(result)
