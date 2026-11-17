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

Deploy a minimal live system containing a public Streamlit UI, FastAPI backend,
PostgreSQL with pgvector, health endpoints, authentication foundation, CI/CD,
Terraform-managed AWS infrastructure, secrets handling, and operational logs.
The chat response may initially be a placeholder.

**Goal:** establish a production-shaped walking skeleton before AI complexity.

## Phase 1 — Deterministic baseline RAG

Define the portfolio corpus and ingestion contract, build deterministic
indexing and vector retrieval, generate evidence-backed answers, display
citations, and deploy the first useful public assistant.

**Goal:** establish a simple, reproducible baseline suitable for comparison.

## Phase 2 — Evaluation foundation

Create and version an evaluation dataset, implement retrieval and answer-quality
metrics, capture latency/token/cost data, and make runs reproducible and
comparable.

**Goal:** make later architectural choices empirical.

The evaluation dataset should begin during Phase 1 rather than being postponed
until all baseline implementation work is complete.

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

- public domain and subdomain;
- production model and embedding providers;
- orchestration framework for bounded agentic retrieval;
- conditions that justify splitting Streamlit and FastAPI into separate ECS
  services;
- conditions that justify additional task count, Multi-AZ RDS, or other
  availability spending.

These decisions are made in the stage where evidence is available and the
choice becomes consequential.

