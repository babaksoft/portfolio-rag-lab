# ADR-0005: Use LlamaIndex for baseline RAG and offline corpus generation

- **Status:** Accepted
- **Date:** 2026-11-27

## Context

Phase 1 needs a reproducible indexing and retrieval path, plus a way to prepare
portfolio material for ingestion. The GenAI Template donor already has
LlamaIndex readers, splitters, and OpenAI adapters, along with a Workflows-based
corpus generator. OpenAI credits are available for development experiments.
The project needs to compare later configurations on the same evidence and
respect the [framework-neutral boundary](0002-framework-neutral-domain-boundary.md).

## Decision

Use LlamaIndex Core and the integrations exercised by the baseline for document
processing and model adapters. Keep ranked pgvector retrieval, evidence selection,
citation mapping, and abstention explicit in the application and its adapters.
Translate framework values at the boundary. Keep PostgreSQL with pgvector as
the durable retrieval store.

Use LlamaIndex Workflows for an offline corpus-generation command. Publish a
versioned, validated corpus artifact for indexing. Keep the source snapshot,
generation configuration, and output identity available for comparison. Adapt
the smallest relevant donor components through the project boundaries.

Use OpenAI for initial development with one generation model and one embedding
model. Select exact model IDs when the corresponding adapter is exercised and
record the IDs in configuration and run evidence. Select the production
provider using measured quality, latency, and cost. Amazon Bedrock is a
candidate for a controlled generator comparison on the same corpus and index.
Evaluate an embedding change with a corresponding index rebuild. The Phase 4
spike will select the bounded-agent orchestration framework.

## Consequences

Donor reuse reduces initial integration work and gives a second framework to
learn alongside LangChain in a separate project. The project owns its corpus
artifact, data contracts, and database integration. Pin compatible dependency
versions in `uv.lock` when introducing each integration. Revisit the choice if
maintaining the adapter boundary or adapting donor components takes more work
than the library saves.

## Alternatives considered

- Direct provider SDKs and a plain Python corpus command would reduce framework
  dependencies. They would require rebuilding or adapting more donor behavior.
- LangChain would cover similar application needs. LlamaIndex offers a closer
  fit to the existing donor code and supports the learning goal for this project.
- Bedrock can provide an AWS-native inference path. Compare it once the OpenAI
  development baseline can measure the tradeoffs.
