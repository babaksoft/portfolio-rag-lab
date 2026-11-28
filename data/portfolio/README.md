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

## Generate and review the showcase corpus

[The source selection](showcase-sources.json) lists the four summary units, full
commit IDs, public origins, and exact input paths. Keep the three repositories
as sibling checkouts or pass `--repositories` with their common parent. The
command reads committed files from the pinned Git trees. Review those files
for publication eligibility before sending them to OpenAI.

```bash
uv run --group corpus python scripts/generate_corpus.py inspect
```

Set `OPENAI_API_KEY` in the checkout's `.env` file using an editor. Git ignores
the file, so keep its access limited to your local account. The `generate`
command loads the key at runtime. A key already supplied by the process
environment takes precedence. Compare the two models using the same Characters
selection. Each run writes a separate candidate and reports its path and corpus
version.

```bash
uv run --group corpus python scripts/generate_corpus.py generate \
  --unit chat-buddy-characters --pilot --confirm-source-review
uv run --group corpus python scripts/generate_corpus.py generate \
  --unit chat-buddy-characters --pilot --model gpt-6.2-sol --confirm-source-review
```

Check both results against the pinned implementation. Trace the evolution
strategy proposal after a completed, selected turn, deterministic application
validation, and how accepted events support replay. Verify the cited file paths
and the distinction between implemented behavior and plans. To experiment with
a different explicit file list or focus, pass `--selection` with a copy of the
selection JSON. Keep the source selection the same for a model comparison.

After the pilot, generate all four units with the final model.

```bash
uv run --group corpus python scripts/generate_corpus.py generate \
  --model gpt-6.2-sol --confirm-source-review
```

`inspect` reports bytes locally. Generation uses the Responses API to count
the actual prompt, and caps each request at 272,000 input and 8,000 billed
output tokens. Narrow overly large selections around the relevant subsystems.
The local `.corpus-work/budget.sqlite` ledger shares a USD 10 limit across runs
from this checkout, with USD 2 available to the pilot within that limit. Keep
the ledger throughout Slice 2. The command reserves the estimated maximum at
Standard uncached rates before sending inference and reconciles reported usage
afterward. An attempt without reported usage keeps its reservation.

Review every generated unit against its pinned inputs. Then author
`evaluation.json` for the exact candidate and verify answerable cases for the
Lab, Support Desk, and both Chat Buddy areas, plus an abstention case. For
example, verify that the case about rolling summaries and user-managed memory
in Chat cites the Chat unit, and that a case about replayable persona evolution
cites Characters. Citation ranges belong to the candidate Markdown. The pinned
Git URL identifies the upstream source tree for review.

```bash
uv run python scripts/validate_corpus.py "$candidate/corpus" "$evaluation"
uv run --group corpus python scripts/generate_corpus.py promote \
  "$candidate" "$evaluation" --version "$approved_version"
```

Use the command's reported candidate directory and the reviewed version and
evaluation path for these values. Promotion validates the corpus, run record,
and evaluation again, then publishes `data/portfolio/releases/<version>/`.
The `corpus/` subdirectory is the input to ingestion. `run.json` beside it
records the source selections, prompt revision, requested and returned model
IDs, reasoning settings, token usage, and corpus version. Keep the approved
bytes for reproduction because `gpt-6.2-sol` is an alias.
