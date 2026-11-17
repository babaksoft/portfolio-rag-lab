# ADR-0001: Adopt a modular application with explicit UI and API boundaries

- **Status:** Accepted
- **Date:** 2026-11-17

## Context

The first release must establish a production-shaped path from a browser to
application behavior without turning the presentation framework into the
application or paying the operational cost of independently deployed services.
The UI must remain replaceable, and later retrieval configurations must be
comparable behind the same application boundary.

## Decision

Build one modular application in one repository and Python distribution. Use a
browser-facing presentation adapter that reaches the backend only through an
explicit API client and HTTP API adapter. Keep use-case coordination in an
application layer, business concepts in the domain, and persistence, retrieval,
and external integrations in outbound adapters.

The initial modules may run in separate processes or containers while
remaining one application. Deployment topology and operational contracts are
specified separately from this source-code boundary.

## Consequences

- UI and transport frameworks can change without moving product rules.
- Retrieval variants share stable use cases and can be evaluated consistently.
- Explicit translation between UI, transport, domain, and persistence types
  adds some code.
- Module boundaries must be reviewed because a single repository does not
  enforce them automatically.

## Alternatives considered

- Put application and data-access logic in the presentation layer. This is
  initially faster but couples behavior to the UI and weakens testability.
- Deploy independently owned services from the start. Current scale and team
  needs do not justify the operational and contract-management cost.
- Let the UI access persistence directly. This bypasses the API and application
  boundaries and makes authorization and behavior inconsistent.
