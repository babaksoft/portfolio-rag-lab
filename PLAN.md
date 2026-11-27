# Portfolio Retrieval Lab — Master Plan

## Delivery model

Each stage is an outcome, not a single large change. Before implementation, the
stage receives a just-in-time plan containing approximately four to eight
reviewable slices. Each slice should introduce one coherent behavior or
operational capability, include its verification, keep the repository green,
and update only documentation whose truth changed.

Review-size heuristics are guidance rather than gates. A slice should normally
stay near 200–500 meaningful changed lines. Changes above roughly 800 meaningful
lines, or changes containing more than one major design decision, should prompt
an explicit split review. Generated files and mechanical changes are evaluated
separately from conceptual complexity.

## Phase 0 — Architecture and deployment skeleton

Deploy a minimal live system with an authenticated Streamlit UI, a FastAPI
backend, PostgreSQL with pgvector, health endpoints, CI/CD, Terraform-managed AWS
infrastructure, secrets handling, and operational logs. The chat response may
initially be a placeholder.

**Goal:** establish a production-shaped walking skeleton before AI complexity.

## Phase 1 — Deterministic baseline RAG

Define the portfolio corpus and ingestion contract, build deterministic
indexing and vector retrieval, generate evidence-backed answers, display
citations, and deploy the first useful public assistant.

The [stage plan](docs/stages/02-phase-1-deterministic-baseline-rag/PLAN.md)
uses the accepted [baseline stack](docs/adr/0005-use-llamaindex-for-baseline-rag.md)
and [telemetry approach](docs/adr/0006-instrument-rag-and-monitor-application-health.md).
Start curating evaluation cases and instrument retrieval and generation as they
land. Target live tracing and a minimum monitoring dashboard before public RAG
availability.

**Goal:** establish a simple, reproducible baseline suitable for comparison.

## Phase 2 — Evaluation foundation

Create and version an evaluation dataset, implement retrieval and answer-quality
metrics, capture latency/token/cost data, and make runs reproducible and
comparable.

**Goal:** make later architectural choices empirical.

Build on the dataset started in Phase 1 with the accepted
[evaluation runner and offline scorer](docs/adr/0007-own-rag-evaluation-and-score-with-ragas.md).

## Phase 3 — Enhanced deterministic RAG

Add deterministic improvements one at a time, such as hybrid retrieval,
metadata filters, query rewriting, reranking, deduplication, evidence thresholds,
and abstention. Retain only improvements that earn their complexity in
evaluation.

**Goal:** determine how far predictable retrieval can go before agentic control
is justified.

## Phase 4 — Bounded agentic retrieval

Run a small external orchestration-framework spike, record the framework
decision, and implement one read-only agent with a constrained retrieval
toolset, strict budgets, full traces, and deterministic termination.

**Goal:** measure agentic retrieval where decomposition or adaptive retries may
provide real value.

## Phase 5 — Comparative routing and production hardening

Compare all supported configurations, introduce a router that selects the least
complex adequate path, harden failure behavior and operations, and publish the
measured tradeoffs.

Non-retrieval routes are limited to clarification, rejection, and capability
explanation. Factual portfolio claims always require evidence.

**Goal:** operate a credible public system and communicate defensible
engineering conclusions.

## Deferred decisions

- production model and embedding providers;
- orchestration framework for bounded agentic retrieval;
- conditions that justify splitting Streamlit and FastAPI into separate ECS
  services;
- conditions that justify additional task count, Multi-AZ RDS, or other
  availability spending.

These decisions are made in the stage where evidence is available and the
choice becomes consequential.
