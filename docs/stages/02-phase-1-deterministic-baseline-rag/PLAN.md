# Phase 1 — Deterministic Baseline RAG

**Status** — Draft for review before implementation

## Outcome

Deploy a useful portfolio assistant that answers from a versioned corpus,
links claims to retrieved evidence, and abstains when the evidence is
insufficient. The baseline uses a fixed retrieval path and configuration so
later approaches can be compared under the same conditions.

## Entry conditions and scope

Begin implementation after [Phase 0 Slice 8 live verification](../01-phase-0-architecture-deployment-skeleton/PLAN.md#slice-8--operational-readiness)
and review this draft against the findings. The proposed
[baseline stack](../../adr/0005-use-llamaindex-for-baseline-rag.md),
[telemetry approach](../../adr/0006-instrument-rag-and-monitor-application-health.md),
and [evaluation approach](../../adr/0007-own-rag-evaluation-and-score-with-ragas.md)
inform the sequence. Resolve the decisions needed by each slice before adding
dependencies or changing the runtime.

Use the existing PostgreSQL, API, UI, and authenticated deployment paths.
Start with single-turn questions. The master plan reserves the repeatable
evaluation runner, judge integration, and quantitative comparisons for Phase 2.
Multi-turn behavior, advanced retrieval, and agent orchestration remain later
work. Decide whether to broaden access separately from proving the baseline
with authorized reviewers.

## Slice 1 — Define the corpus and initial evaluation cases

**Outcome** — Establish which source material the assistant can use as evidence
and what a correct answer should cover.

**Scope and artifacts** — Select a small set of publishable portfolio sources.
Define the versioned corpus artifact, source identities and citation locations,
and validation rules. Prepare a small seed artifact and hand-authored cases
covering answerable questions, expected sources and facts, and abstention.

**Verification and completion** — Validate the seed artifact and confirm that
the expected evidence and citation targets in the cases resolve to that corpus
version. Review a case where the corpus has insufficient evidence.

**Documentation** — Record source eligibility and the corpus and case formats
beside the artifacts.

## Slice 2 — Generate a corpus artifact offline

**Outcome** — Produce a reviewable corpus from a known source snapshot.

**Scope and artifacts** — Adapt the relevant donor workflow steps for an offline
command. Record source versions, generation configuration, and output identity.
Validate the generated artifact and review factual fidelity before promoting it
for ingestion. Use the seed artifact and a fake model in routine tests.

**Verification and completion** — Generate and validate a small artifact using
the command. Check that rejected output leaves the previous valid artifact
available. Review a bounded run with the configured development model.

**Documentation** — Document invocation, review and publication, and what is
recorded for reruns.

## Slice 3 — Index the corpus and retrieve evidence

**Outcome** — Run one ranked vector query against an identifiable index built
from the corpus.

**Scope and artifacts** — Introduce the retrieval schema and migration, chunking
configuration, one embedding adapter, repeatable ingestion, and pgvector top-k
retrieval. Record the corpus version and embedding configuration associated with
the index. Capture retrieval timing and outcome from the first working path.

**Verification and completion** — In a migrated PostgreSQL instance, index the
fixture, verify its expected evidence ranks for known queries, and check stable
source links. Verify repeat indexing avoids duplicate active evidence and a
failed rebuild preserves the usable index. Run the normal suite with fake
provider calls and run the database integration check separately.

**Documentation** — Record the indexing and rebuild commands and schema contract.

## Slice 4 — Generate cited answers through the API and UI

**Outcome** — An authorized user can ask an answerable question, inspect its
citations, and get an explicit abstention for an unsupported question.

**Scope and artifacts** — Connect retrieval to the message use case, add one
generation adapter, and validate proposed citations against selected evidence.
Render citations and abstentions in Streamlit. Bound provider timeouts and map
provider failures to safe outcomes. Capture generation timing, outcome, and
token usage where available.

**Verification and completion** — Exercise the UI-to-API path with fixtures for
supported, unsupported, invalid-citation, and provider-failure cases. Check that
citations resolve to sources retrieved for the request and errors remain safe.
Smoke-test a bounded real-provider request using the small corpus.

**Documentation** — Update local setup and the implemented answer and citation
contracts.

## Slice 5 — Verify request traces and service metrics

**Outcome** — Follow an individual request in Phoenix and see service behavior
over time in Grafana.

**Scope and artifacts** — Connect the existing timings and outcomes to a local
Phoenix instance and Prometheus collection. Provision one Grafana dashboard for
request rate, errors, latency, and provider timeouts. Estimate live hosting and
retention costs using the observed telemetry volume. Plan initial alert rules
using observed failure modes and verify notification delivery when enabled.

**Verification and completion** — Generate a success and a controlled failure.
Match a trace to the corresponding request log and observe both requests in
the collected metrics. Inspect exported spans and metric labels for raw content
and identity data. Verify that a telemetry outage leaves the RAG request path
available.

**Documentation** — Record local setup, sample queries, the dashboard location,
and the live hosting decision.

## Slice 6 — Deploy and verify the baseline

**Outcome** — The deployed assistant serves the reviewed corpus, with an
operational baseline ready for Phase 2 measurement.

**Scope and artifacts** — Define how to load the reviewed corpus and rebuild or
restore the known-good index after a cold reconstruction. Verify model access,
usage limits, and the migration and rollback path. Deploy through the approved
production workflow and bring up the minimum live telemetry setup. If starting
with a supervised reviewer pilot, record its scope and any remaining telemetry
work before opening public access.

**Verification and completion** — Complete authenticated live smoke checks for
cited answers, abstention, and safe failure. Confirm model, corpus, and index
configuration, safe traces, and collected metrics under representative requests.
Check that the previous healthy revision remains compatible with the migration
and index choices. Record the observed baseline and any deviations.

**Documentation** — Update the relevant deployment and recovery procedures,
and record live evidence and Phase 2 follow-ups in the implementation record.

## Stage completion

An end-to-end deployed baseline can be reproduced from a known corpus and
configuration. Cited answers and abstentions are verified, minimum live traces
and metrics are available, and the versioned dataset is ready for Phase 2.
