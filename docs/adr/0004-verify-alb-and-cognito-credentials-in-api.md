# ADR-0004: Verify ALB and Cognito credentials in FastAPI

- **Status:** Accepted
- **Date:** 2026-11-22

## Context

Production uses an Application Load Balancer in front of Streamlit and a
task-local FastAPI process. The load balancer can complete Cognito
authentication and signs the user claims that it forwards, but its assertion
contains user-info claims rather than Cognito's token-only group claims.
Authorization must use the `reviewers` Cognito group, and neither Streamlit
state nor unsigned identity headers are an acceptable backend trust boundary.

## Decision

The ALB performs Cognito authentication before forwarding normal UI traffic.
Streamlit forwards both `x-amzn-oidc-data` and
`x-amzn-oidc-accesstoken` over task-local HTTP without storing or logging them.
FastAPI verifies the ALB assertion's ES256 signature, signer ARN, client ID,
expiry, and subject. It separately verifies the Cognito access token's RS256
signature, issuer, client ID, token use, expiry, and subject. The subjects must
match, and the access token must contain the `reviewers` group before FastAPI
resolves the subject to an application-owned identity.

The `/auth/logout` listener rule is the only public route forwarded directly to
FastAPI. It expires all possible ALB session-cookie shards and redirects through
Cognito's logout endpoint. All product operations remain task-local and
FastAPI-owned.

## Consequences

- Client-controlled identity headers and Streamlit session state cannot grant
  backend access.
- Authorization remains in FastAPI while authentication and browser-session
  refresh remain at the load balancer and Cognito boundary.
- FastAPI fetches and caches public signing keys from fixed regional AWS
  endpoints; key rotation does not require application deployment.
- Every protected UI-to-API call carries two credentials over task-local HTTP.
  They must never be logged or persisted.
- Local development explicitly disables authentication. Production startup
  requires every signer and issuer trust anchor.
- Changing the ALB, user pool, or app client requires updating the ECS task
  configuration before the replacement task can authorize requests.

## Alternatives considered

- Trust the unsigned ALB subject header. A caller with any path to FastAPI could
  forge it, so it cannot establish an identity.
- Trust only the ALB assertion. Its user-info payload does not carry Cognito's
  token-only group membership, so it cannot enforce the required group.
- Make Streamlit authorize requests. This contradicts the established backend
  authorization boundary and makes UI state security-sensitive.
- Query Cognito for group membership on every request. This introduces a paid,
  failure-prone network dependency when the already signed access token carries
  the required claim.
