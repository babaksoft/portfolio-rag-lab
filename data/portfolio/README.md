# Portfolio corpus and evaluation cases

## Source eligibility

Use portfolio material that is approved for publication, relevant to the
project, and reviewable at an immutable revision. Check facts against that
revision and exclude secrets, private material, and personal data unrelated to
the portfolio. The seed contains two verbatim ADRs from the MIT-licensed GenAI
Template donor. Each manifest entry links to the exact Git commit and source
path. The repository license records the shared copyright and license terms.

## Corpus format

Each corpus lives in a flat directory with `manifest.json` and one UTF-8
Markdown file per source. The manifest has `schema_version: 1` and an ordered
`sources` array. Each source records a unique `source_id`, its public HTTPS
`origin_url` at an immutable revision, and the lowercase SHA-256
`content_sha256` of the exact Markdown bytes. Use lower kebab case for IDs.
Store each source as `<source_id>.md` and preserve its ID across revisions of
the same logical source.

The corpus version is the SHA-256 of the validated manifest serialized as
UTF-8 JSON with sorted keys, compact separators, and no terminal newline.
Source order, provenance, and file hashes all contribute to the version.
Publish changed evidence as a new corpus version and review its cases again.

## Evaluation format

`evaluation.json` has `schema_version: 1`, the exact `corpus_version`, and a
`cases` array. Each case gives a unique lower-kebab-case `case_id`, a
`question`, and an `expected_outcome` of `answer` or `abstain`. Answerable
cases require `required_facts` and `expected_evidence`. Abstention cases leave
both arrays empty or omit them.

Each evidence reference contains `source_id`, `start_line`, and `end_line`.
The endpoints are inclusive and numbered from one using LF line breaks in the
artifact Markdown. Because the seed files are verbatim, those ranges also
identify lines in the linked donor files. The retention question is an
abstention case because the seed ADRs explain snapshots and corpus layout but
give no retention period.

Validate the seed locally:

```bash
uv run python scripts/validate_corpus.py data/portfolio/seed-v1/corpus data/portfolio/seed-v1/evaluation.json
```

The command checks artifact integrity and that every expected citation resolves
in the pinned corpus. Review source eligibility and factual support separately.
