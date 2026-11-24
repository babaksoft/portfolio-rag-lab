import asyncio
import json
from uuid import UUID

import httpx
import pytest

from portfolio_rag.api import create_app
from portfolio_rag.api.settings import ApiSettings
from portfolio_rag.application import (
    AuthenticationError,
    AuthorizationError,
    IdentityResolver,
    IdentityVerifier,
)
from portfolio_rag.domain import AuthenticatedPrincipal, Identity


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
    settings: ApiSettings | None = None,
    identity_verifier: IdentityVerifier | None = None,
    identity_resolver: IdentityResolver | None = None,
    raise_app_exceptions: bool = True,
) -> httpx.Response:
    transport = httpx.ASGITransport(
        app=create_app(
            settings=settings,
            readiness_probe=_ReadinessProbe(database_ready),
            identity_verifier=identity_verifier,
            identity_resolver=identity_resolver,
        ),
        raise_app_exceptions=raise_app_exceptions,
    )
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        return await client.request(method, path, json=json, headers=headers)


class _IdentityVerifier:
    def __init__(self, failure: Exception | None = None) -> None:
        self._failure = failure

    async def verify(
        self, identity_assertion: str, access_token: str
    ) -> AuthenticatedPrincipal:
        assert identity_assertion == "signed-edge-assertion"
        assert access_token == "signed-access-token"
        if self._failure is not None:
            raise self._failure
        return AuthenticatedPrincipal(
            external_subject="stable-subject",
            email="reviewer@example.com",
        )


class _IdentityResolver:
    def __init__(self) -> None:
        self.principal: AuthenticatedPrincipal | None = None

    async def execute(self, principal: AuthenticatedPrincipal) -> Identity:
        self.principal = principal
        return Identity(
            id=UUID("11111111-1111-1111-1111-111111111111"),
            external_subject=principal.external_subject,
            email=principal.email,
        )


def _authenticated_settings() -> ApiSettings:
    return ApiSettings(
        authentication_mode="alb_cognito",
        alb_arn="arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/test/1",
        cognito_user_pool_id="us-east-1_example",
        cognito_client_id="client-id",
        cognito_domain="portfolio-rag.auth.us-east-1.amazoncognito.com",
        application_url="https://portfolio.example.com/signed-out",
    )


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


def test_request_log_is_structured_correlated_and_content_free(
    capsys: pytest.CaptureFixture[str],
) -> None:
    response = asyncio.run(
        _request(
            "POST",
            "/v1/messages",
            json={"message": "private portfolio question"},
            headers={"X-Correlation-ID": "logged-correlation"},
        )
    )

    records = [json.loads(line) for line in capsys.readouterr().err.splitlines()]
    request_record = next(
        record for record in records if record["event"] == "request_completed"
    )
    assert response.status_code == 200
    assert request_record["service"] == "portfolio-rag-api"
    assert request_record["correlation_id"] == "logged-correlation"
    assert request_record["http_path"] == "/v1/messages"
    assert request_record["http_status"] == 200
    assert "private portfolio question" not in json.dumps(records)


def test_malformed_message_returns_bounded_error() -> None:
    response = asyncio.run(_request("POST", "/v1/messages", json={"message": "   "}))

    assert response.status_code == 422
    assert response.json()["code"] == "invalid_request"
    assert response.json()["message"] == "The request payload is invalid."
    assert response.json()["correlation_id"]
    assert "input" not in response.text


def test_unsafe_incoming_correlation_id_is_replaced() -> None:
    response = asyncio.run(
        _request(
            "POST",
            "/v1/messages",
            json={"message": "Hello"},
            headers={"X-Correlation-ID": "unsafe user content"},
        )
    )

    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] != "unsafe user content"
    assert response.json()["correlation_id"] == response.headers["X-Correlation-ID"]


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


def test_protected_message_requires_both_credentials() -> None:
    response = asyncio.run(
        _request(
            "POST",
            "/v1/messages",
            json={"message": "Hello"},
            settings=_authenticated_settings(),
            identity_verifier=_IdentityVerifier(),
            identity_resolver=_IdentityResolver(),
        )
    )

    assert response.status_code == 401
    assert response.json()["code"] == "authentication_required"


def test_protected_message_resolves_verified_internal_identity(
    capsys: pytest.CaptureFixture[str],
) -> None:
    resolver = _IdentityResolver()
    response = asyncio.run(
        _request(
            "POST",
            "/v1/messages",
            json={"message": "Hello"},
            headers={
                "X-Correlation-ID": "authenticated-correlation",
                "X-Amzn-Oidc-Data": "signed-edge-assertion",
                "X-Amzn-Oidc-AccessToken": "signed-access-token",
            },
            settings=_authenticated_settings(),
            identity_verifier=_IdentityVerifier(),
            identity_resolver=resolver,
        )
    )

    assert response.status_code == 200
    assert resolver.principal is not None
    assert resolver.principal.external_subject == "stable-subject"
    records = [json.loads(line) for line in capsys.readouterr().err.splitlines()]
    for event in ("authentication_verified", "identity_resolved"):
        record = next(item for item in records if item["event"] == event)
        assert record["correlation_id"] == "authenticated-correlation"


def test_invalid_or_unauthorized_credentials_fail_safely() -> None:
    for failure, expected_status in (
        (AuthenticationError("forged"), 401),
        (AuthorizationError("not a reviewer"), 403),
    ):
        response = asyncio.run(
            _request(
                "POST",
                "/v1/messages",
                json={"message": "Hello"},
                headers={
                    "X-Amzn-Oidc-Data": "signed-edge-assertion",
                    "X-Amzn-Oidc-AccessToken": "signed-access-token",
                },
                settings=_authenticated_settings(),
                identity_verifier=_IdentityVerifier(failure),
                identity_resolver=_IdentityResolver(),
            )
        )

        assert response.status_code == expected_status
        assert "forged" not in response.text
        assert "not a reviewer" not in response.text


class _FailingIdentityResolver:
    async def execute(self, principal: AuthenticatedPrincipal) -> Identity:
        del principal
        raise RuntimeError("database password must stay private")


def test_unexpected_failure_returns_bounded_correlated_error() -> None:
    response = asyncio.run(
        _request(
            "POST",
            "/v1/messages",
            json={"message": "Hello"},
            headers={
                "X-Correlation-ID": "failure-correlation",
                "X-Amzn-Oidc-Data": "signed-edge-assertion",
                "X-Amzn-Oidc-AccessToken": "signed-access-token",
            },
            settings=_authenticated_settings(),
            identity_verifier=_IdentityVerifier(),
            identity_resolver=_FailingIdentityResolver(),
            raise_app_exceptions=False,
        )
    )

    assert response.status_code == 500
    assert response.json() == {
        "code": "internal_error",
        "message": "The request could not be completed.",
        "correlation_id": "failure-correlation",
    }
    assert "database password" not in response.text


def test_logout_expires_alb_cookie_shards_and_uses_cognito() -> None:
    response = asyncio.run(
        _request(
            "GET",
            "/auth/logout",
            settings=_authenticated_settings(),
            identity_verifier=_IdentityVerifier(),
            identity_resolver=_IdentityResolver(),
        )
    )

    assert response.status_code == 303
    assert response.headers["location"].startswith(
        "https://portfolio-rag.auth.us-east-1.amazoncognito.com/logout?"
    )
    assert (
        "logout_uri=https%3A%2F%2Fportfolio.example.com%2Fsigned-out"
        in (response.headers["location"])
    )
    cookies = response.headers.get_list("set-cookie")
    assert len(cookies) == 5
    assert all("Max-Age=0" in cookie for cookie in cookies)
