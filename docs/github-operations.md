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

## Later AWS delivery through OIDC

Phase 0 Slice 6 will add the AWS delivery path. GitHub Actions must exchange its
short-lived OIDC token for scoped AWS roles; do not create or store long-lived
AWS access keys in GitHub secrets.

The AWS trust policy must restrict the GitHub OIDC audience to `sts.amazonaws.com`
and restrict the subject to this repository and the exact approved branch or
protected GitHub environment. Separate roles should grant only the permissions
needed by CI, publishing, and deployment. Deployment workflows must request
`id-token: write` only at the job that assumes a role, pin actions to immutable
revisions, use protected production-environment approval, and deploy immutable
image references. Terraform will manage the OIDC provider, roles, and trust
policy when that slice is implemented.
