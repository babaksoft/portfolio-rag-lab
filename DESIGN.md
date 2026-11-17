# Portfolio Retrieval Lab — Design

## Purpose

This document describes the current durable architecture and the boundaries
that implementation must preserve. Update it when component responsibilities,
dependency direction, or system boundaries change. Record the reason for a
consequential choice in an [ADR](docs/adr/README.md) rather than duplicating its
history here.

The repository currently contains only the Python and quality foundation. The
structure below is the agreed direction for the application as it is built.

## Application structure

```text
browser
  -> UI adapter
  -> explicit API client
  -> HTTP API adapter
  -> application use cases
  -> domain
       <- persistence, retrieval, and external-provider adapters
```

The corresponding package structure is:

```text
src/portfolio_rag/
├── domain/
├── application/
│   └── services/
├── api/
├── ui/
└── infrastructure/
    ├── db/
    │   ├── models/
    │   └── repositories/
    ├── retrieval/
    └── providers/
```

Create these packages when their first real component is implemented; do not
add empty structure in anticipation of later stages.

- `ui` owns rendering and browser interaction, not product rules or data
  access. `api` owns inbound HTTP transport and validation. Both are inbound
  adapters and remain outside `infrastructure`.
- The HTTP API adapter validates transport data and invokes application use
  cases. Transport models do not become domain models by convenience.
- The application layer coordinates use cases and transactions in domain terms.
  Each use case is implemented as a narrow, verb-led `*Service` class under
  `application/services/` with one public `execute()` operation. Broad services
  must not accumulate unrelated operations.
- The domain owns business vocabulary, invariants, and the interfaces needed
  by use cases. Name behavior by its role—such as `*Policy`, `*Strategy`, or
  `*Validator`—and reserve `*Service` for domain behavior that belongs to no
  entity or value object.
- `infrastructure` contains outbound adapters, grouped by capability. These
  adapters implement application-owned interfaces for persistence, retrieval,
  and external services and translate framework or provider types at the
  boundary.

Dependencies point inward: adapters may depend on application and domain code;
application code may depend on the domain; the domain does not depend on UI,
web, persistence, cloud, or AI orchestration frameworks. See
[ADR-0001](docs/adr/0001-modular-application-shape.md) and
[ADR-0002](docs/adr/0002-framework-neutral-domain-boundary.md).

## Evolution rules

- Add an interface when a real use case needs a boundary, not in anticipation
  of a possible provider or framework.
- Keep framework configuration and lifecycle code at an adapter or composition
  boundary.
- Keep conversation context, retrieved evidence, and provider payloads as
  distinct concepts as their contracts are introduced.
- Revise this document when implementation changes the architecture. Supersede
  an accepted ADR with a new ADR when the underlying decision changes.

Detailed runtime, persistence, identity, configuration, observability, and
deployment contracts are intentionally deferred to the next bootstrap step.

## Documentation ownership

| Document | Owns | Update when |
| --- | --- | --- |
| `README.md` | Reviewer entry point and local setup | The first-use path changes |
| `VISION.md` | Product charter, principles, and non-goals | Strategic intent changes |
| `PLAN.md` | Outcome-oriented delivery roadmap | Phase outcomes or order change |
| `DESIGN.md` | Current architecture and boundaries | Architectural truth changes |
| `docs/adr/` | Consequential decision history | A decision is made or superseded |
| `docs/stages/` | Stage plans and implementation records | Stage intent or results change |
| `AGENTS.md` | Durable repository working conventions | Commands or conventions change |
