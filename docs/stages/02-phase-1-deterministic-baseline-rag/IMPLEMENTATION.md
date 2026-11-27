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
