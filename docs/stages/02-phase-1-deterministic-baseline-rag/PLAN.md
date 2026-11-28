# Phase 1 — Deterministic Baseline RAG

**Status** — In progress

## Outcome

Deploy a useful portfolio assistant that answers from a versioned corpus,
links claims to retrieved evidence, and abstains when the evidence is
insufficient. The baseline uses a fixed retrieval path and configuration so
later approaches can be compared under the same conditions.

## Entry conditions and scope

Phase 0 Slice 8 [live verification](../01-phase-0-architecture-deployment-skeleton/PLAN.md#slice-8--operational-readiness)
is complete. The accepted
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

**Status:** — Complete (2026-11-27)

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

**Outcome** — Publish a reviewed corpus covering three showcase projects from
pinned source snapshots.

**Scope and artifacts** — Keep the existing flat corpus and manifest formats.
Use four explicit summary units with stable project-prefixed source IDs. The
following revisions are starting candidates for the source review.

| Source ID | Candidate revision | Initial coverage |
| --- | --- | --- |
| `portfolio-rag-lab-overview` | [Portfolio Retrieval Lab](https://github.com/babaksoft/portfolio-rag-lab/tree/14a1c694aed4a0c7c702203ec316b5e3693d9c42) | Purpose, architecture, and implemented capabilities |
| `support-desk-overview` | [Support Desk](https://github.com/babaksoft/support-desk/tree/89f23f7c01ac8f274092481d6f0357e8fd13d2d2) | Current product-guidance use case and OpenAI Agents SDK integration, with planned experiments identified as such |
| `chat-buddy-chat` | [Chat Buddy](https://github.com/babaksoft/chat-buddy/tree/b2c9e91ab8563c28b79e9c4b786ed8b2a58bafe6/src/chat_buddy/chat) | Context budgeting, rolling summaries, and Chat memory |
| `chat-buddy-characters` | [Chat Buddy](https://github.com/babaksoft/chat-buddy/tree/b2c9e91ab8563c28b79e9c4b786ed8b2a58bafe6/src/chat_buddy/characters) | Conversation modes, relationship evolution, and persona adaptations |

Adapt the donor's committed snapshot selection, explicit summary units, and
generation steps into an offline LlamaIndex Workflows command under the
[accepted baseline stack](../../adr/0005-use-llamaindex-for-baseline-rag.md).
Keep GenAI Template as the workflow reference and the existing seed as a test
fixture. Read explicit file selections from Git commits. Start with the README,
relevant design decisions, entry points, and implementation files that support
each unit. For large inputs, split by subsystem and retain the original evidence
needed for synthesis. Use each unit's public commit-pinned tree as its manifest
origin. Record the exact input paths for review. Evaluation citations use the
generated Markdown's line numbers.

**Model and budget** — Use `gpt-5.4-mini-2026-03-17` for prompt and input
experiments. Use `gpt-6.2-sol` with medium reasoning for the final candidate,
with access to the same pinned source evidence. Select one model per run. Adapt
the donor's OpenAI Responses adapter to use model-specific settings and output
limits in place of its fixed temperature. Record the requested and returned
model IDs, reasoning settings, prompt revision, source selection, token usage,
and output corpus version for each successful run. Sol's configured ID is an
alias, so retain the approved artifact as the record of its exact output.

Cap total Slice 2 inference at USD 10 and reserve up to USD 2 for the pilot.
Count assembled input tokens before inference. Check the remaining budget before
each paid request using the applicable rates, the input count, and the maximum
billed output, including reasoning. Bound retries and account for usage across
experiments, the pilot, and the final run. Reserve the estimated maximum cost
when a sent request fails without returning usage.

**Verification and completion** — Generate and validate a small candidate with
the seed and a fake model. Before any paid run, review the selected files for
[source eligibility](../../../data/portfolio/README.md#source-eligibility) and
confirm access to the configured model. Compare Mini and Sol on the same Chat
Buddy Characters flow using the same inputs and expected facts. Use evolution
after a completed, selected turn. Check that the summary traces the strategy
proposal, application validation, and replayable accepted events across modules.
Require file references for key claims and a clear distinction between
implemented features and plans.

Stage the generated corpus and keep run records beside it. Validate the artifact
and review all four units against the pinned sources. Check answerable cases for
each project, including a case that requires the correct Chat Buddy area, and
include an abstention case. Pin the cases to the approved artifact version.
Promote the validated directory as a new immutable version for ingestion after
review. Verify that rejected output leaves the previous valid corpus available.

**Documentation** — Document command invocation, spend controls, review and
promotion, and the run record used for reruns.

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
