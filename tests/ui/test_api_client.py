import httpx
import pytest

from portfolio_rag.ui import ApiClientError, PortfolioApiClient, UiSettings


def test_api_client_sends_and_returns_typed_message() -> None:
    def handle_request(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-Correlation-ID"] == "ui-correlation"
        assert request.headers["X-Amzn-Oidc-Data"] == "edge-assertion"
        assert request.headers["X-Amzn-Oidc-AccessToken"] == "access-token"
        assert request.content == b'{"message":"Hello"}'
        return httpx.Response(
            200,
            json={
                "answer": "Placeholder response",
                "is_placeholder": True,
                "correlation_id": "ui-correlation",
            },
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

    assert result.answer == "Placeholder response"
    assert result.is_placeholder is True
    assert result.correlation_id == "ui-correlation"


def test_api_client_translates_unavailable_backend() -> None:
    def fail_request(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("private diagnostic detail")

    client = PortfolioApiClient(
        UiSettings(), transport=httpx.MockTransport(fail_request)
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
        lambda _request: httpx.Response(200, json={"answer": "untyped"})
    )
    client = PortfolioApiClient(UiSettings(), transport=transport)

    with pytest.raises(ApiClientError) as captured:
        client.answer_message("Hello")

    assert captured.value.code == "invalid_backend_response"
