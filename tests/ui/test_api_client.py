from unittest.mock import Mock

import httpx
import pytest

from portfolio_rag.ui import ApiClientError, PortfolioApiClient, UiSettings


def _fail_request(_request: httpx.Request) -> httpx.Response:
    raise httpx.ConnectError("private diagnostic detail")


def test_api_client_sends_and_returns_typed_message() -> None:
    handle_request = Mock(
        return_value=httpx.Response(
            200,
            json={
                "answer": "Placeholder response",
                "is_placeholder": True,
                "correlation_id": "ui-correlation",
            },
        )
    )
    client = PortfolioApiClient(
        UiSettings(), transport=httpx.MockTransport(handle_request)
    )

    result = client.answer_message(
        "Hello",
        correlation_id="ui-correlation",
        identity_assertion="edge-assertion",
        access_token="access-token",
    )

    assert handle_request.call_count == 1
    (request,) = handle_request.call_args.args
    assert request.headers["X-Correlation-ID"] == "ui-correlation"
    assert request.headers["X-Amzn-Oidc-Data"] == "edge-assertion"
    assert request.headers["X-Amzn-Oidc-AccessToken"] == "access-token"
    assert request.content == b'{"message":"Hello"}'
    assert result.answer == "Placeholder response"
    assert result.is_placeholder is True
    assert result.correlation_id == "ui-correlation"


def test_api_client_translates_unavailable_backend() -> None:
    client = PortfolioApiClient(
        UiSettings(), transport=httpx.MockTransport(_fail_request)
    )

    with pytest.raises(ApiClientError) as captured:
        client.answer_message("Hello")

    assert captured.value.code == "backend_unavailable"
    assert captured.value.user_message == (
        "The assistant is temporarily unavailable. Please try again."
    )
    assert "private diagnostic detail" not in captured.value.user_message


def test_api_client_rejects_invalid_backend_contract() -> None:
    transport = httpx.MockTransport(
        Mock(return_value=httpx.Response(200, json={"answer": "untyped"}))
    )
    client = PortfolioApiClient(UiSettings(), transport=transport)

    with pytest.raises(ApiClientError) as captured:
        client.answer_message("Hello")

    assert captured.value.code == "invalid_backend_response"


@pytest.mark.parametrize(
    ("status", "code", "message"),
    [
        (401, "authentication_required", "Sign out, then sign in again"),
        (403, "access_denied", "not authorized as a reviewer"),
        (500, "backend_error", "Please try again"),
    ],
)
def test_api_client_distinguishes_authentication_and_backend_failures(
    status: int, code: str, message: str
) -> None:
    client = PortfolioApiClient(
        UiSettings(),
        transport=httpx.MockTransport(Mock(return_value=httpx.Response(status))),
    )

    with pytest.raises(ApiClientError) as captured:
        client.answer_message("Hello")

    assert captured.value.code == code
    assert message in captured.value.user_message
