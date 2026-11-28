# Phase 1 — Implementation

## Slice 1 — Corpus and initial evaluation cases

- The [seed corpus](../../../data/portfolio/README.md) contains two verbatim
  donor ADRs from commit `da75642211959a54e6c26b6df71d459ae0f14f26`.
  Each source has an ID, a commit-pinned public origin, and a content hash.
- Adapted the donor's flat manifest layout and content verification. The
  evaluation dataset pins the manifest hash and cites Markdown line ranges
  within that version.
- Checked both answerable cases against the cited lines. Reviewed the retention
  question for abstention because neither selected source gives a retention
  period.
- The offline validator verified both documents and all three cases. Tests
  cover modified and extra files, mismatched versions, invalid citation ranges,
  and inconsistent answer or abstention expectations.

## Slice 2 — Offline corpus generation

- Added an offline LlamaIndex Workflows command for committed source selection,
  candidate generation, and separate reviewed promotion. It reuses the existing
  corpus and evaluation validators. The default selection reads all four units
  from the intended public Git revisions.
- Added the OpenAI Responses adapter with model-specific reasoning, input and
  output limits, and a durable local spend ledger. The seed-and-fake workflow
  and mocked provider tests exercise staging, rejected output, preservation of
  an approved release, and budget behavior across retries.
- The command loads its OpenAI key from the checkout's ignored `.env` or the
  process environment. Credential loading was verified with synthetic values.
  The paid Characters comparison, four-unit generation, and review of the
  showcase artifact and its pinned cases remain pending. See the
  [corpus run instructions](../../../data/portfolio/README.md#generate-and-review-the-showcase-corpus).
