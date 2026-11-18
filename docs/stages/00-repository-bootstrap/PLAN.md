# Repository Bootstrap Stage Plan

## Purpose

Prepare Portfolio Retrieval Lab for implementation without prematurely choosing
AI providers, orchestration frameworks, or advanced retrieval techniques. The
result should be a clean, understandable repository whose scope, standards,
architecture boundaries, and first implementation stage are explicit.

This repository uses `master` as its default branch. Coding agents must not
create commits unless the user explicitly requests one.

## Completion criteria

Repository bootstrap is complete when:

- project identity, vision, scope, and non-goals are recorded;
- engineering and agent conventions are explicit;
- Python and quality-tool configuration is reproducible;
- the documentation and ADR structure exists;
- initial architectural decisions are recorded without over-designing later
  retrieval stages;
- Phase 0 has a sliced, independently verifiable stage plan;
- GitHub CI and dependency-maintenance policy are defined;
- no unresolved decision blocks the first implementation slice.

## Step 1 — Establish repository identity and project charter

**Status:** Complete

- Create `~/projects/portfolio-rag-lab`.
- Initialize Git with `master` as the local branch.
- Add a reviewer-oriented `README.md`.
- Record the full project charter in `VISION.md`.
- Record the outcome-oriented delivery roadmap in the root `PLAN.md`.
- Preserve the baseline, enhanced deterministic, bounded agentic, evaluation,
  production-routing, multi-turn conversation, cloud, and donor-reuse decisions.

**Verification:** the repository exists, the expected documents are readable,
Git whitespace validation passes, and the working branch is `master`.

## Step 2 — Establish repository and coding-agent conventions

**Status:** Complete

- Add a concise root `AGENTS.md` containing only durable, non-obvious commands,
  constraints, and conventions.
- Record Python 3.12, `uv`, `src` layout, absolute imports, and naming rules.
- Require complete type hints and Google-style docstrings for first-party
  production classes and callables, with the agreed narrow exemptions.
- Record Pydantic field-description and persistence-field documentation rules.
- Record the small-slice review policy and the rule against agent-created commits
  without explicit approval.
- Add an appropriate `.gitignore`, `.editorconfig`, and placeholder
  `.env.example` without secrets.
- Decide and record the repository license before publishing publicly.

**Verification:** a new coding session can determine how to work safely in the
repository without referring to conversation history.

## Step 3 — Configure the Python and quality foundation

**Status:** Complete

- Create `pyproject.toml` for Python 3.12 and package `portfolio_rag`.
- Use `uv` for dependency and environment management.
- Configure Ruff for formatting, import ordering, linting, and docstring rules;
  do not add Black or isort.
- Configure strict, practical mypy checks and pytest defaults.
- Add the minimal package and test directories needed to validate configuration,
  without introducing application architecture prematurely.
- Add a single local quality-check command or script.
- Generate and retain the `uv` lockfile.

**Verification:** environment synchronization, formatting checks, linting, type
checking, and the empty/minimal test suite all succeed from documented commands.

## Step 4 — Establish the living-document and ADR system

**Status:** Complete

- Add `DESIGN.md` for durable architecture and boundary explanations.
- Create a concise ADR directory, template, and index.
- Record only decisions that are already consequential, including the initial
  application shape and framework-neutral domain boundary.
- Define the convention for per-stage plans and parallel implementation records.
- Keep `README.md` reviewer-oriented; avoid duplicating detailed design text.

**Verification:** every document has a distinct purpose and a clear update
trigger; the same decision is not maintained independently in several places.

## Step 5 — Record the initial architecture contracts

**Status:** Complete

- Describe the Streamlit, API-client, FastAPI, PostgreSQL/pgvector, and external
  provider boundaries.
- Record the initial two-container, single-task ECS/Fargate deployment shape and
  its deliberate availability limitations.
- Record the multi-turn conversation requirement and the distinction between
  conversational context and retrieved evidence.
- Define high-level configuration, secrets, logging, health, and identity
  contracts without implementing them.
- Identify which choices remain deferred to the stage where evidence makes them
  consequential.

**Verification:** Phase 0 can be planned without inventing missing component
ownership or coupling business logic to Streamlit, AWS, or an LLM framework.

## Step 6 — Prepare the sliced Phase 0 implementation plan

**Status:** Complete

- Create the Phase 0 stage plan immediately before implementation.
- Break it into approximately four to eight coherent, independently verifiable
  slices.
- Give every slice an outcome, scope boundary, expected artifacts, verification,
  documentation impact, and completion condition.
- Include the local walking skeleton, containerization, database foundation,
  AWS foundation, deployment, CI/CD, authentication, and operational readiness
  without combining them into one oversized diff.
- Create an initially empty Phase 0 implementation record for results,
  deviations, incidents, and follow-up work.

**Verification:** the first slice can begin without unresolved scope questions,
and later slices remain adjustable based on learning.

## Step 7 — Prepare GitHub repository operations

**Status:** Complete

- Create or connect the GitHub repository only when explicitly requested.
- Add CI for formatting, linting, typing, and tests.
- Configure GitHub Actions with least privilege and pin actions appropriately.
- Configure Dependabot for the `uv` and `github-actions` ecosystems with weekly,
  grouped routine updates and a small pull-request limit.
- Enable the dependency graph, Dependabot alerts, and security updates in GitHub
  repository settings.
- Do not enable automatic dependency-update merging.
- Document the later AWS OIDC setup; do not store long-lived AWS credentials in
  GitHub.

**Verification:** pull requests receive deterministic quality feedback, and
dependency changes remain visible and manually reviewed.

## Step 8 — Run the pre-implementation readiness review

**Status:** Complete

Results and remaining risks are recorded in
[`IMPLEMENTATION.md`](IMPLEMENTATION.md).

- Run every documented local quality command.
- Check for secrets and accidental donor-repository artifacts.
- Confirm that deferred decisions are genuinely non-blocking.
- Confirm that Phase 0 Slice 1 has a narrow, testable completion condition.
- Review the complete bootstrap diff before the user commits it.
- Record any remaining risks or deliberate compromises.

**Verification:** the repository is clean, reproducible, internally consistent,
and ready for the first implementation slice.

## Deferred beyond repository bootstrap

- application implementation and container images;
- AWS resource creation or Terraform application;
- model and embedding-provider selection;
- portfolio corpus ingestion;
- retrieval and evaluation implementation;
- orchestration-framework comparison;
- domain registration and public DNS selection.

These belong to their corresponding delivery phases rather than repository
bootstrap.
