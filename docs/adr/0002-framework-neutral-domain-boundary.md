# ADR-0002: Keep the domain boundary framework-neutral

- **Status:** Accepted
- **Date:** 2026-11-17

## Context

The project will compare retrieval approaches and may change web, persistence,
AI-provider, or orchestration technology over time. If framework models and
provider payloads become the application's core vocabulary, those experiments
will force unrelated business logic and tests to change.

## Decision

Express domain concepts and repository protocols in Python types owned by the
domain. Domain dependencies are limited to the standard library, Pydantic, and
the domain itself. Application code can also depend on the domain and owns the
use cases and application-specific contracts.

Outbound adapters translate external types at their owning boundary and can
import application contracts, values, and errors. The HTTP API calls
application use cases and uses domain types needed at the HTTP boundary. The UI
accesses the backend over HTTP. Composition wires concrete dependencies and
owns the API lifecycle. Runtime adapters and composition may share the
structured-logging helper. The full rules are in
[Design](../../DESIGN.md#source-dependencies).

Introduce interfaces only for capabilities required by a concrete use case.
Do not create speculative abstractions solely to make every dependency
replaceable.

## Consequences

- Domain behavior can be tested without infrastructure or provider SDKs.
- Framework and provider changes remain localized to adapters and composition.
- Pytest enforces import direction and checks package re-exports by parsing
  source without starting the application.
- Boundary mapping is explicit and adds modest implementation overhead.
- Developers must resist passing convenient framework objects through use-case
  and domain APIs.

## Alternatives considered

- Reuse transport or ORM models throughout the application. This reduces early
  mapping code but couples business behavior to boundary concerns.
- Adopt an orchestration framework's abstractions as the domain. No framework
  has yet earned that central role, and doing so would bias later comparisons.
- Abstract every external dependency immediately. This would create interfaces
  without use cases to prove their shape.
