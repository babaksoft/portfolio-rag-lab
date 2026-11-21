# GitHub Repository Operations

This document records repository-level automation and security settings. Update
it when CI triggers, dependency-maintenance policy, or GitHub-to-AWS trust
changes.

## Quality feedback

The `Quality` workflow runs on every pull request and every push to `master`.
It executes `./scripts/quality.sh`, so local and hosted checks use the same
locked environment and formatting, linting, typing, and test commands. The
workflow grants only read access to repository contents, does not persist the
checkout credential, pins third-party actions to full commit SHAs, and pins the
installed `uv` version.

The workflow's `Python quality checks` job is required by the default-branch
ruleset and must report from the GitHub Actions app. Dependabot checks the `uv`
and GitHub Actions ecosystems weekly, groups routine updates by ecosystem, and
limits each ecosystem to three open version-update pull requests. Dependency
updates remain visible for manual review; automatic merging is not enabled.

The `Container build` workflow has the same triggers and independently builds
both runtime images from their production Dockerfiles. The default-branch
ruleset should require its `Build runtime images` job alongside `Python quality
checks` so a pull request cannot merge when either locked application checks or
either production image fails to build.

Repository-level Actions permissions default to read-only, and workflows may
not use `GITHUB_TOKEN` to approve pull requests. A future workflow must declare
any narrower write permission at the job that needs it.

The repository settings keep the dependency graph, Dependabot alerts, and
Dependabot security updates enabled. These settings complement the committed
Dependabot version-update schedule: alerts identify vulnerable dependencies,
and security updates may open focused remediation pull requests outside the
weekly routine-update grouping.

## Default-branch and merge policy

The active `Protect master` ruleset targets the default branch and has no bypass
actors. Changes must arrive through pull requests, but zero approving reviews
are required for the current solo-maintainer workflow. All review conversations
must be resolved, and the strict `Python quality checks` status must pass
against the latest `master` before merge.

The ruleset blocks branch deletion, force pushes, and merge commits. Repository
merge settings allow only squash merges, automatically delete merged head
branches, and keep automatic merging disabled. Each focused pull request
therefore becomes one linear commit on `master` after explicit review and merge.

Required commit signing remains deliberately deferred. Reconsider it after
local Git signing is configured and both a normal pull request and a Dependabot
pull request have demonstrated verified commits throughout the merge path.
Enabling the rule earlier could block otherwise valid work containing an
unsigned commit, even when the pull request would be squash-merged.

## AWS delivery through OIDC

The manually dispatched `Deploy production` workflow accepts only a commit that
is reachable from `master`. It serializes production runs without canceling an
active deployment, builds and publishes API and UI images under the immutable
`sha-<full-commit>` tag, creates a saved Terraform plan, and pauses at the
protected `production` environment before applying that exact artifact. All
third-party actions are pinned to full commit SHAs. No AWS access key is stored
in GitHub.

The bootstrap Terraform root references the account-level GitHub OIDC provider
and manages three roles:

- `portfolio-rag-github-publish` can publish only the two application ECR
  repositories and trusts only workflows whose ref is `master`;
- `portfolio-rag-github-plan` has read-only AWS and production-state access,
  cannot lock or write state, and has the same `master` trust restriction;
- `portfolio-rag-github-deploy` is capped by the Terraform operator boundary;
  it can pass only the two application task roles, run only the migration task
  family, and update only the one production service. It trusts only this
  repository's `production` GitHub Environment.

Every trust policy requires the `sts.amazonaws.com` audience and GitHub's
immutable owner-and-repository-ID subject prefix. Jobs request `id-token: write`
only when they assume one of these roles. The plan gate
accepts exactly two ECS task-definition replacements and one ECS service
update; any network, IAM, database, DNS, or other infrastructure change fails
closed and must follow the separately reviewed manual Terraform path.

Before the first dispatch, apply the reviewed bootstrap plan with the
administrative bootstrap identity, then create a `production` GitHub
Environment with a required reviewer and no branch other than `master`.
Update the default-branch ruleset to require `Build runtime images`. These live
changes must be performed and recorded separately because merging workflow
files does not mutate AWS or repository settings.

The deployment runs the new API image's backward-compatible Alembic migrations
before applying the plan. ECS circuit-breaker rollback handles an unhealthy
replacement; the workflow additionally restores the service's previous task
definition when Terraform apply or digest verification fails. It verifies the
running API and UI digests against ECR after the service stabilizes. A failed
migration occurs before the service update and therefore leaves the running
revision unchanged. Database migrations are not automatically reversible.

To roll back an application revision, manually dispatch the workflow from
`master` with the last known healthy commit SHA. The existing immutable images
are reused, a new saved plan is reviewed at the environment gate, and the same
migration, apply, health, and digest checks run. Never select a revision whose
schema is incompatible with the database's current migration level.
