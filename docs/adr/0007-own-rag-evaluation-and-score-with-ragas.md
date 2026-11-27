# ADR-0007: Own RAG evaluation and score with Ragas

- **Status:** Proposed
- **Date:** 2026-11-27

## Context

The project compares retrieval configurations using the same versioned cases.
The donor has a retrieval evaluator with deterministic ranking metrics. This
project also needs to check groundedness, required facts, citations, and
abstention. An evaluation run should be inspectable and repeatable without
depending on a live tracing or evaluation server.

## Decision

Start a hand-authored dataset in Phase 1 with expected evidence, required facts,
and answer or abstention expectations. In Phase 2, build a small runner that
executes the normal RAG path, computes deterministic checks such as recall@k
and citation validity, and persists per-case results. Record dataset and corpus
versions, configurations, model IDs, latency, usage, and the judge settings
needed to interpret the results. Evaluate saved outputs separately when
changing the scorer.

Use Ragas as an offline scorer over project-owned run artifacts. Start with
Faithfulness to assess support from the supplied context. Check factual coverage
and citation validity separately. Compare judge responses with hand-reviewed
examples before using aggregate scores to select a configuration. Add custom
rubrics only when a concrete evaluation question requires them.

## Consequences

The runner makes dataset construction, metric inputs, and failures visible while
Ragas supplies a practical starting scorer. Judge calls introduce cost and
variability. Keep the judge and rubric fixed when comparing configurations and
preserve case-level results for diagnosing disagreement. Revisit the scorer if
it repeatedly disagrees with hand-reviewed cases or cannot express a needed
rubric.

## Alternatives considered

- TruLens is a fit for evaluation driven by application traces. The first
  benchmark can score saved outputs while Phoenix handles trace diagnosis.
- Giskard is a fit for generated scenarios and exploring coverage gaps after
  the project establishes its curated benchmark.
- Custom judge implementations give full control over prompts and scoring.
  Start with the small runner and an existing scorer to learn both the
  evaluation mechanics and how to validate a third-party metric.
