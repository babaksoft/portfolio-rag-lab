# ADR-0002: Keep the domain boundary framework-neutral

- **Status:** Accepted
- **Date:** 2026-11-17

## Context

The project will compare retrieval approaches and may change web, persistence,
AI-provider, or orchestration technology over time. If framework models and
provider payloads become the application's core vocabulary, those experiments
will force unrelated business logic and tests to change.

## Decision

Express domain concepts and required interfaces in application-owned Python
types. Domain code must not import UI, HTTP, persistence, cloud, model-provider,
or orchestration frameworks. Adapters translate external types at their owning
boundary and depend inward on the interfaces they implement.

Introduce interfaces only for capabilities required by a concrete use case.
Do not create speculative abstractions solely to make every dependency
replaceable.

## Consequences

- Domain behavior can be tested without infrastructure or provider SDKs.
- Framework and provider changes remain localized to adapters and composition.
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
