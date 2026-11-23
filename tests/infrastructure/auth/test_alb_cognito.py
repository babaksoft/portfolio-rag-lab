import asyncio
import json
import time

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from jwt.algorithms import RSAAlgorithm

from portfolio_rag.application import AuthenticationError, AuthorizationError
from portfolio_rag.infrastructure.auth import AlbCognitoIdentityVerifier

REGION = "us-east-1"
POOL_ID = "us-east-1_example"
CLIENT_ID = "client-id"
ALB_ARN = (
    "arn:aws:elasticloadbalancing:us-east-1:123456789012:"
    "loadbalancer/app/portfolio/1234"
)


def _credentials(groups: list[str]) -> tuple[str, str, httpx.MockTransport]:
    now = int(time.time())
    subject = "11111111-2222-3333-4444-555555555555"
    alb_private_key = ec.generate_private_key(ec.SECP256R1())
    alb_public_key = alb_private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    cognito_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    cognito_jwk = json.loads(RSAAlgorithm.to_jwk(cognito_private_key.public_key()))
    cognito_jwk["kid"] = "cognito-key"

    assertion = jwt.encode(
        {"sub": subject, "email": "reviewer@example.com"},
        alb_private_key,
        algorithm="ES256",
        headers={
            "kid": "alb-key",
            "signer": ALB_ARN,
            "client": CLIENT_ID,
            "exp": now + 300,
        },
    )
    access_token = jwt.encode(
        {
            "sub": subject,
            "iss": f"https://cognito-idp.{REGION}.amazonaws.com/{POOL_ID}",
            "client_id": CLIENT_ID,
            "token_use": "access",
            "cognito:groups": groups,
            "exp": now + 300,
        },
        cognito_private_key,
        algorithm="RS256",
        headers={"kid": "cognito-key"},
    )

    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/alb-key":
            return httpx.Response(200, content=alb_public_key)
        return httpx.Response(200, json={"keys": [cognito_jwk]})

    return assertion, access_token, httpx.MockTransport(respond)


def _verifier(transport: httpx.MockTransport) -> AlbCognitoIdentityVerifier:
    return AlbCognitoIdentityVerifier(
        region=REGION,
        load_balancer_arn=ALB_ARN,
        user_pool_id=POOL_ID,
        client_id=CLIENT_ID,
        required_group="reviewers",
        transport=transport,
    )


def test_verifies_matching_reviewer_credentials() -> None:
    assertion, access_token, transport = _credentials(["reviewers"])

    principal = asyncio.run(_verifier(transport).verify(assertion, access_token))

    assert principal.external_subject == "11111111-2222-3333-4444-555555555555"
    assert principal.email == "reviewer@example.com"


def test_rejects_verified_principal_outside_reviewers() -> None:
    assertion, access_token, transport = _credentials(["other-group"])

    with pytest.raises(AuthorizationError):
        asyncio.run(_verifier(transport).verify(assertion, access_token))


def test_rejects_client_controlled_identity_assertion() -> None:
    _assertion, access_token, transport = _credentials(["reviewers"])

    with pytest.raises(AuthenticationError):
        asyncio.run(_verifier(transport).verify("forged", access_token))
