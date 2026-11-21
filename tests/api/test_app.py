import asyncio

import httpx

from portfolio_rag.api import create_app


class _ReadinessProbe:
    def __init__(self, ready: bool) -> None:
        self._ready = ready

    async def is_ready(self) -> bool:
        return self._ready


async def _request(
    method: str,
    path: str,
    *,
    json: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    database_ready: bool = True,
) -> httpx.Response:
    transport = httpx.ASGITransport(
        app=create_app(readiness_probe=_ReadinessProbe(database_ready))
    )
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        return await client.request(method, path, json=json, headers=headers)


def test_message_crosses_api_boundary_with_correlation_id() -> None:
    response = asyncio.run(
        _request(
            "POST",
            "/v1/messages",
            json={"message": "What did you build?"},
            headers={"X-Correlation-ID": "test-correlation"},
        )
    )

    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] == "test-correlation"
    assert response.json() == {
        "answer": (
            "Placeholder response: portfolio retrieval is not implemented yet, "
            "so this is not a factual answer."
        ),
        "is_placeholder": True,
        "correlation_id": "test-correlation",
    }


def test_malformed_message_returns_bounded_error() -> None:
    response = asyncio.run(_request("POST", "/v1/messages", json={"message": "   "}))

    assert response.status_code == 422
    assert response.json()["code"] == "invalid_request"
    assert response.json()["message"] == "The request payload is invalid."
    assert response.json()["correlation_id"]
    assert "input" not in response.text


def test_health_endpoints_report_process_health() -> None:
    for path in ("/health/live", "/health/ready"):
        response = asyncio.run(_request("GET", path))
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "service": "portfolio-rag-api"}


def test_failed_readiness_does_not_change_liveness() -> None:
    readiness_response = asyncio.run(
        _request("GET", "/health/ready", database_ready=False)
    )
    liveness_response = asyncio.run(
        _request("GET", "/health/live", database_ready=False)
    )

    assert readiness_response.status_code == 503
    assert readiness_response.json() == {
        "status": "unavailable",
        "service": "portfolio-rag-api",
    }
    assert liveness_response.status_code == 200
    assert liveness_response.json()["status"] == "ok"
