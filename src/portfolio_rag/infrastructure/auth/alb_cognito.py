"""Verification for ALB identity assertions and Cognito access tokens."""

import re
import time
from typing import cast

import httpx
import jwt
from jwt import InvalidTokenError, PyJWK

from portfolio_rag.application import AuthenticationError, AuthorizationError
from portfolio_rag.domain import AuthenticatedPrincipal

_KEY_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


class AlbCognitoIdentityVerifier:
    """Verify the trusted edge and Cognito credentials for one request."""

    def __init__(
        self,
        *,
        region: str,
        load_balancer_arn: str,
        user_pool_id: str,
        client_id: str,
        required_group: str,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        """Configure expected issuers, signers, and authorization group.

        Args:
            region:
                AWS region containing the ALB and Cognito user pool.
            load_balancer_arn:
                Exact trusted signer ARN expected in the ALB JWT header.
            user_pool_id:
                Cognito user pool whose access tokens are accepted.
            client_id:
                Cognito app client used by the ALB authentication action.
            required_group:
                Cognito group required for application authorization.
            transport:
                Optional HTTP transport used by isolated tests.
        """
        self._load_balancer_arn = load_balancer_arn
        self._client_id = client_id
        self._required_group = required_group
        self._issuer = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"
        self._alb_key_base_url = f"https://public-keys.auth.elb.{region}.amazonaws.com"
        self._transport = transport
        self._alb_keys: dict[str, str] = {}
        self._cognito_keys: dict[str, PyJWK] = {}

    async def verify(
        self, identity_assertion: str, access_token: str
    ) -> AuthenticatedPrincipal:
        """Verify both credentials, their shared subject, and group membership.

        Raises:
            AuthenticationError:
                If either credential fails cryptographic or semantic validation.
            AuthorizationError:
                If the verified access token lacks the required Cognito group.
        """
        try:
            assertion_header = cast(
                dict[str, object], jwt.get_unverified_header(identity_assertion)
            )
            self._validate_assertion_header(assertion_header)
            assertion_key = await self._get_alb_key(self._key_id(assertion_header))
            assertion_claims = cast(
                dict[str, object],
                jwt.decode(
                    identity_assertion,
                    assertion_key,
                    algorithms=["ES256"],
                    options={
                        "require": ["sub"],
                        "verify_aud": False,
                        "verify_exp": False,
                    },
                ),
            )

            access_header = cast(
                dict[str, object], jwt.get_unverified_header(access_token)
            )
            access_key = await self._get_cognito_key(self._key_id(access_header))
            access_claims = cast(
                dict[str, object],
                jwt.decode(
                    access_token,
                    access_key.key,
                    algorithms=["RS256"],
                    issuer=self._issuer,
                    options={"require": ["exp", "iss", "sub"], "verify_aud": False},
                ),
            )
            self._validate_access_claims(access_claims)
        except (
            InvalidTokenError,
            KeyError,
            TypeError,
            ValueError,
            httpx.HTTPError,
        ) as error:
            raise AuthenticationError("Credentials could not be verified.") from error

        assertion_subject = self._required_string(assertion_claims, "sub")
        access_subject = self._required_string(access_claims, "sub")
        if assertion_subject != access_subject:
            raise AuthenticationError("Credential subjects do not match.")
        if len(assertion_subject) > 128:
            raise AuthenticationError("The credential subject is invalid.")

        groups = access_claims.get("cognito:groups", [])
        if not isinstance(groups, list) or self._required_group not in groups:
            raise AuthorizationError("The principal lacks the required group.")

        email_value = assertion_claims.get("email")
        email = email_value if isinstance(email_value, str) else None
        if email is not None and len(email) > 320:
            raise AuthenticationError("The credential email is invalid.")
        return AuthenticatedPrincipal(external_subject=assertion_subject, email=email)

    def _validate_assertion_header(self, header: dict[str, object]) -> None:
        """Reject assertions not signed for this exact application edge."""
        if header.get("alg") != "ES256":
            raise AuthenticationError("Unexpected assertion algorithm.")
        if header.get("signer") != self._load_balancer_arn:
            raise AuthenticationError("Unexpected assertion signer.")
        if header.get("client") != self._client_id:
            raise AuthenticationError("Unexpected assertion client.")
        expiration = header.get("exp")
        if isinstance(expiration, bool) or not isinstance(
            expiration, str | int | float
        ):
            raise AuthenticationError("The edge assertion has expired.")
        try:
            expiration_timestamp = float(expiration)
        except ValueError as error:
            raise AuthenticationError("The edge assertion has expired.") from error
        if expiration_timestamp <= time.time():
            raise AuthenticationError("The edge assertion has expired.")

    def _validate_access_claims(self, claims: dict[str, object]) -> None:
        """Reject Cognito tokens issued for another use or client."""
        if claims.get("token_use") != "access":
            raise AuthenticationError("An access token is required.")
        if claims.get("client_id") != self._client_id:
            raise AuthenticationError("Unexpected access-token client.")

    async def _get_alb_key(self, key_id: str) -> str:
        """Return a cached ALB public key from the fixed regional endpoint."""
        if key_id not in self._alb_keys:
            async with httpx.AsyncClient(
                transport=self._transport, timeout=3.0
            ) as client:
                response = await client.get(f"{self._alb_key_base_url}/{key_id}")
                response.raise_for_status()
            self._alb_keys[key_id] = response.text
        return self._alb_keys[key_id]

    async def _get_cognito_key(self, key_id: str) -> PyJWK:
        """Return a cached Cognito signing key from the pool's JWKS document."""
        if key_id not in self._cognito_keys:
            async with httpx.AsyncClient(
                transport=self._transport, timeout=3.0
            ) as client:
                response = await client.get(f"{self._issuer}/.well-known/jwks.json")
                response.raise_for_status()
            document = response.json()
            if not isinstance(document, dict) or not isinstance(
                document.get("keys"), list
            ):
                raise ValueError("Cognito returned an invalid JWKS document.")
            for raw_key in document["keys"]:
                if isinstance(raw_key, dict):
                    parsed_key = PyJWK.from_dict(raw_key)
                    if parsed_key.key_id is not None:
                        self._cognito_keys[parsed_key.key_id] = parsed_key
        try:
            return self._cognito_keys[key_id]
        except KeyError as error:
            raise AuthenticationError("The Cognito signing key is unknown.") from error

    @staticmethod
    def _key_id(header: dict[str, object]) -> str:
        """Return a bounded signing-key identifier safe for URL construction."""
        key_id = header.get("kid")
        if not isinstance(key_id, str) or _KEY_ID_PATTERN.fullmatch(key_id) is None:
            raise AuthenticationError("The signing-key identifier is invalid.")
        return key_id

    @staticmethod
    def _required_string(claims: dict[str, object], name: str) -> str:
        """Return one required non-empty string claim."""
        value = claims.get(name)
        if not isinstance(value, str) or not value:
            raise AuthenticationError(f"The {name} claim is invalid.")
        return value
