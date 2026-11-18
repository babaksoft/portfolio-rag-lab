# Phase 0 — Implementation Record

Add dated entries only when implementation begins. Keep results, deviations,
incidents, deliberate compromises, and follow-up work factual and link to
durable design documents rather than repeating them here.

## Results

### 2026-11-18 — Slice 1 local walking skeleton

- Added a Streamlit entry point, an explicit typed HTTP client, a FastAPI entry
  point, and the narrow `AnswerMessageService`. The returned text is visibly
  labeled as a non-factual placeholder.
- Added typed environment settings, bounded transport models and errors,
  correlation-ID propagation, and dependency-free liveness and readiness.
- Selected FastAPI and Streamlit because the durable design already requires
  those delivery adapters. Selected HTTPX for the explicit synchronous UI
  client and Pydantic Settings for typed environment loading; both integrate
  directly with FastAPI's Pydantic transport boundary without another
  abstraction layer.
- Declared Pydantic as a direct dependency because first-party production code
  imports it. Application results and UI boundary results use immutable
  Pydantic models consistently rather than mixing Pydantic with dataclasses.
- Kept `api/app.py` as a composition root and separated health and message
  routers, dependency accessors, correlation handling, and safe error
  translation into focused API modules.
- Added unit and boundary coverage for the application service, API validation
  and health, successful client serialization, backend unavailability, and an
  invalid backend response.
- `./scripts/quality.sh` passed with 8 tests. Both documented process commands
  started successfully; API liveness, API readiness, and Streamlit health
  returned successfully. A Streamlit test-harness submission crossed the real
  HTTP client and running FastAPI process and displayed the placeholder with
  its correlation identifier preserved at the API boundary.

### 2026-11-18 — Slice 2 containerized local runtime

- Added separate multi-stage API and UI images. Each installs only locked
  runtime dependencies, contains the installed application rather than a source
  bind mount, and runs as the dedicated numeric user `10001`.
- Added Compose orchestration with loopback-only published ports, dependency-
  ordered startup, image-level health checks, and a ten-second stop grace
  period. The UI reaches the API through `PORTFOLIO_RAG_UI_API_BASE_URL` at the
  Compose service address, preserving the configuration boundary intended for
  task-local ECS networking.
- Added a minimized build context and a bounded smoke command that builds and
  starts the runtime, waits for health, verifies both runtime identities, calls
  the backend through the UI-owned typed client, and stops both containers.
- Selected Debian slim Python images for compatibility with the locked Python
  dependencies and copied a version-pinned `uv` binary only into build stages;
  neither build tooling nor development dependencies are present at runtime.
- A clean local build and `uv run python scripts/container_smoke.py` passed.
  Both image
  health checks became healthy, the task-local-style client call returned the
  placeholder, both containers ran as UID `10001`, no local `.env` or build
  tool was present, and both containers stopped within the configured grace
  period.

## Deviations

None.

## Incidents

None.

## Deliberate compromises

- Readiness currently matches liveness because Slice 1 has no external runtime
  dependency. The database slice will add its first dependency check.
- The UI shows only the current exchange; durable conversation identity and
  history remain deferred until a use case requires them.

## Follow-up work

- When image build time becomes material in CI or deployment, separate the
  locked third-party dependency layer from the first-party package install and
  add a BuildKit cache mount for uv downloads. Docker's standard layer cache is
  sufficient for the intentionally small walking skeleton, so that complexity
  is deferred until measurements justify it.
