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

## Boundary contracts

### Streamlit UI

- Streamlit owns rendering, user interaction, and presentation-only session
  state. It does not implement use cases, authorize actions, query the database,
  or call external AI providers.
- All backend operations go through the explicit API client under `ui/`. No
  other UI code issues HTTP requests or depends on FastAPI internals.
- The UI may present conversation history and citations returned by the API,
  but it does not decide what qualifies as evidence.

### API client

- The API client owns backend URL configuration, HTTP serialization,
  credentials or identity-context propagation, timeouts, and translation of
  transport failures into UI-facing errors.
- It exposes typed, task-oriented operations to Streamlit rather than raw HTTP
  primitives. It does not expose FastAPI request objects or backend persistence
  types.
- Local and deployed backend addresses differ by configuration; UI behavior
  must not depend on the network topology.

### FastAPI API

- FastAPI is the backend HTTP entry point. It owns routing, transport-model
  validation, authenticated-principal extraction, and translation between HTTP
  and application types.
- Route handlers invoke application services and contain no product rules,
  retrieval strategy, transaction logic, or direct database access.
- API responses use explicit transport models and never expose ORM, pgvector,
  provider-SDK, or unfiltered exception types.

### PostgreSQL and pgvector

- PostgreSQL is the durable relational store; pgvector supplies vector storage
  and similarity search inside that store. Neither technology defines domain
  or application-layer types.
- Only adapters under `infrastructure/db/` issue queries. Mapped models remain
  under `infrastructure/db/models/`, and repository implementations remain
  under `infrastructure/db/repositories/`.
- Repository protocols use domain language. Database adapters translate rows,
  identifiers, nullability, and transaction failures at the boundary.
- Schema migrations are the source of truth for persistent structure once the
  database slice introduces them. Application startup must not mutate schema.

### External providers

- Model, embedding, and future orchestration integrations live under
  `infrastructure/providers/` and implement interfaces owned by the application
  core. Provider SDK types do not cross that boundary.
- Adapters own provider authentication, request/response translation, bounded
  timeouts and retries, usage metadata, and provider-specific error mapping.
- Use cases own semantic policy and budgets. Providers do not decide whether
  evidence is sufficient, whether a factual claim is allowed, or whether an
  agent may continue.
- Provider selection remains configuration and must not require changes to
  domain behavior.

## Conversation and evidence contracts

- A conversation has a stable identity and an ordered message history. Each
  request identifies the conversation and the new user turn explicitly.
- Conversation history helps resolve references and intent; it is never, by
  itself, evidence for a factual portfolio claim.
- Retrieved evidence is represented separately from messages and provider
  payloads. It retains enough source identity and location information to
  support citations and retrieval traces.
- Every factual portfolio claim must be supported by evidence selected for the
  current turn. A prior answer or citation may guide retrieval but does not
  remove this requirement.
- Application services own context selection, retrieval coordination, and the
  association between an answer and its cited evidence. The UI only renders the
  resulting contract.
- Persistence must keep conversation messages, retrieval traces, and cited
  evidence distinguishable; an unstructured prompt is not the system of record.

## Runtime and deployment contract

The initial production runtime is one ECS/Fargate service with desired task
count one. Each task contains two containers: Streamlit for the UI and FastAPI
for the backend. They are deployed and scaled as one unit and communicate over
the task-local network through the explicit API client. An Application Load
Balancer is the public entry point; PostgreSQL remains an external managed
dependency.

This shape deliberately favors cost and learning speed over availability. A
container or task failure can interrupt the whole application; deployments may
reduce or briefly remove capacity; UI and API cannot scale independently; and
the initial database and task footprint do not promise multi-AZ resilience.
Health checks, bounded shutdown, and recoverable deployment remain required,
but they do not make a single task highly available. See
[ADR-0003](docs/adr/0003-co-locate-ui-and-api-in-one-ecs-task.md).

## Operational contracts

### Configuration and secrets

- Each process loads typed settings at its composition boundary and fails fast
  at startup when required configuration is missing or invalid. Domain and
  application modules do not read environment variables.
- Environment variables are the runtime configuration interface. Safe names
  and placeholders belong in `.env.example`; local `.env` files remain ignored.
- Secret values come from AWS Secrets Manager in production and are injected at
  runtime. Secrets must not appear in source, images, Terraform state output,
  logs, health responses, or client-visible errors.

### Logging

- Containers write structured logs to standard output and error for CloudWatch
  collection. Logs include stable event names, severity, service identity, and
  correlation identifiers needed to follow a request across UI, API, database,
  and provider boundaries.
- Authentication material, secrets, and raw conversation or portfolio content
  are not logged by default. Operational metadata such as latency, outcome,
  provider usage, and bounded error categories is preferred.
- User-facing errors remain safe and stable; diagnostic detail belongs in
  correlated server logs.

### Health

- Each container exposes distinct liveness and readiness signals suitable for
  ECS and load-balancer checks. Liveness reports process health without calling
  dependencies.
- Readiness is fast and bounded and checks only dependencies required to serve
  traffic. It does not make paid model calls or depend on optional providers.
- Health responses contain no secrets, user data, or detailed infrastructure
  errors. Dependency diagnostics belong in logs.

### Identity

- Amazon Cognito is the production identity authority and federates Google
  sign-in. The external subject is mapped to a stable internal identity rather
  than used directly as the domain identifier.
- The trusted edge or API verifies authentication. FastAPI owns authorization
  for backend operations; Streamlit may display identity state but must not be
  the authorization boundary.
- The API client propagates the required credential or verified identity
  context without persisting or logging it. The precise token and edge-flow
  mechanism is selected in the Phase 0 authentication slice.

## Deferred decisions

The following choices do not block the first implementation slice:

| Decision | Resolve when |
| --- | --- |
| ORM, migration, settings, and HTTP-client libraries | The Phase 0 slice first requiring each capability |
| Database schema, vector dimensions, and index type | The database and baseline-retrieval slices |
| Exact API payloads, error codes, and versioning mechanism | The use case introducing each endpoint |
| Cognito token propagation and load-balancer authentication flow | The Phase 0 authentication slice |
| Model and embedding providers | The deterministic baseline stage |
| Agent orchestration framework | The bounded-agentic retrieval spike |
| Public domain and DNS name | Before public deployment requires them |
| Separate ECS services, additional tasks, or Multi-AZ spending | When measured reliability or scaling needs justify them |

## Evolution rules

- Add an interface when a real use case needs a boundary, not in anticipation
  of a possible provider or framework.
- Keep framework configuration and lifecycle code at an adapter or composition
  boundary.
- Keep conversation context, retrieved evidence, and provider payloads as
  distinct concepts as their contracts are introduced.
- Revise this document when implementation changes the architecture. Supersede
  an accepted ADR with a new ADR when the underlying decision changes.

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
