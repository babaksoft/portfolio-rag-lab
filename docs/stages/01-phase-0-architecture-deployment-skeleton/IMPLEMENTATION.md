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

- Slice 2 will package the two verified process commands as separate local
  containers without changing the application boundary.
