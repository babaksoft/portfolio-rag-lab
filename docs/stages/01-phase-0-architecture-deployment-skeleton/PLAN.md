# Phase 0 — Architecture and Deployment Skeleton

## Purpose

Build and deploy the smallest production-shaped system that proves the
repository's application, data, delivery, identity, and operational boundaries
before retrieval or model complexity is introduced.

The durable architecture is defined in [`DESIGN.md`](../../../DESIGN.md) and
[ADR-0003](../../adr/0003-co-locate-ui-and-api-in-one-ecs-task.md). This plan
owns implementation sequence and verification, not those decisions.

## Stage outcome

A user can authenticate and reach a public Streamlit UI backed by FastAPI and
PostgreSQL/pgvector on AWS. The UI and API run as two containers in one
single-task ECS/Fargate service. Quality checks, container delivery, deployment,
health, secrets, and structured logs follow repeatable paths. The chat response
may remain an explicitly non-factual placeholder.

## Scope boundaries

Phase 0 establishes the walking skeleton only. It does not ingest portfolio
content, call model or embedding providers, implement retrieval, claim factual
portfolio knowledge, create an evaluation dataset, or add high availability.
Provider and orchestration-framework choices remain deferred.

Library choices deferred by `DESIGN.md` are made in the first slice that needs
them, using the smallest option compatible with the existing contracts. Record
the choice and evidence in `IMPLEMENTATION.md`; create an ADR only when the
decision is consequential and difficult to reverse.

A public hostname, Google OAuth client, and authorized AWS access are external
prerequisites for the later deployment and authentication slices, not for the
local walking skeleton. Cloud creation or mutation requires explicit user
approval. If a prerequisite is unavailable, later slices may be prepared and
verified locally but cannot be marked complete.

## Slice 1 — Local walking skeleton

**Status:** Not started

### Outcome

A local browser request crosses Streamlit, the explicit API client, FastAPI,
and one narrow application service and returns a clearly labeled placeholder.

### Scope boundary

Implement only the packages and configuration needed by this path. Include
typed transport models, safe error translation, correlation propagation, and
basic process health. Do not add persistence, containers, authentication,
retrieval, provider SDKs, or speculative domain abstractions.

### Expected artifacts

- Streamlit and FastAPI entry points under `ui/` and `api/`;
- a typed API client owned by `ui/`;
- one verb-led application service with an `execute()` operation;
- typed startup settings and safe placeholder environment variables;
- unit and API-boundary tests plus documented local run commands;
- updated dependency declarations and lockfile.

### Verification

- Run `./scripts/quality.sh`.
- Start both processes from documented commands and verify their health.
- Submit a request through Streamlit and confirm it traverses the API client and
  FastAPI before displaying the placeholder.
- Confirm malformed input and an unavailable backend produce bounded,
  user-safe errors.

### Documentation impact

Update `README.md`, `.env.example`, and `IMPLEMENTATION.md`. Change `DESIGN.md`
only if implementation invalidates a boundary.

### Completion condition

A fresh local checkout can synchronize dependencies, run the two processes,
exercise the end-to-end placeholder path, and pass all automated checks without
database or cloud access.

## Slice 2 — Containerized local runtime

**Status:** Not started

### Outcome

The UI and API run locally as separate production-like containers using the
same configuration boundary expected in ECS.

### Scope boundary

Add reproducible images and local composition for the existing path. Use
locked dependencies, non-root runtime users, minimal build contexts, explicit
ports, bounded shutdown, and container health checks. Do not introduce the
database, AWS resources, or a container registry.

### Expected artifacts

- separate UI and API Dockerfiles and entry commands;
- `.dockerignore` and local container orchestration configuration;
- task-local-style API address configuration;
- container health and graceful-shutdown behavior;
- image build and runtime smoke tests.

### Verification

- Build both images from a clean Docker cache and inspect them for embedded
  local configuration or secrets.
- Start the composed runtime, verify container health, and exercise the complete
  UI-to-API placeholder path.
- Stop the runtime and confirm both processes terminate within their configured
  grace period.
- Run `./scripts/quality.sh`.

### Documentation impact

Document container prerequisites and local commands in `README.md`; record
image choices and results in `IMPLEMENTATION.md`.

### Completion condition

One documented command builds and starts the two-container local system, its
health checks pass, and the behavior matches the non-containerized path.

## Slice 3 — PostgreSQL and pgvector foundation

**Status:** Not started

### Outcome

The backend has a migration-controlled PostgreSQL/pgvector connection and a
real readiness dependency without leaking persistence types into the core.

### Scope boundary

Choose the data-access and migration libraries, add local PostgreSQL with
pgvector, establish connection and transaction configuration, and enable the
extension through migrations. Add only schema required by Phase 0 behavior;
identity-specific persistence may wait for Slice 7. Do not add portfolio tables,
embeddings, vector indexes, ingestion, or retrieval behavior.

### Expected artifacts

- PostgreSQL/pgvector local service and safe connection settings;
- migration configuration and an initial reversible migration;
- database lifecycle code under `infrastructure/db/`;
- API readiness behavior that distinguishes dependency failure from liveness;
- integration tests against an isolated database.

### Verification

- Create an empty database, apply all migrations, and verify the pgvector
  extension is available.
- Revert and reapply reversible project migrations where the selected tooling
  supports it.
- Run integration tests and verify no test depends on developer-local state.
- Stop PostgreSQL and confirm readiness fails safely while liveness remains
  responsive; restart it and confirm recovery.
- Run `./scripts/quality.sh`.

### Documentation impact

Update local database setup, `.env.example`, and migration commands. Record the
library decision and migration results in `IMPLEMENTATION.md`.

### Completion condition

A fresh environment can start PostgreSQL/pgvector, migrate from empty state,
run the integration suite, and demonstrate correct liveness/readiness behavior.

## Slice 4 — Terraform-managed AWS foundation

**Status:** Not started

### Outcome

AWS foundation resources are reproducible, least-privileged, cost-conscious,
and ready to host the two-container application.

### Scope boundary

Create the minimal Terraform structure for remote state, networking, security
groups, ECR, ECS cluster capacity, PostgreSQL/pgvector on RDS, Secrets Manager,
CloudWatch log groups, narrowly scoped IAM, Route 53, and ACM. The hostname must
be selected before its DNS zone and certificate are applied. Do not create the
task definition, ECS service, application load balancer, Cognito resources, or
delivery workflow yet.

### Expected artifacts

- version-constrained Terraform configuration and environment inputs;
- documented state bootstrap and locking procedure;
- minimal network and security boundaries;
- ECR repositories, ECS cluster, RDS, secrets, logs, IAM, and common tags;
- cost and destructive-change review notes.

### Verification

- Run Terraform formatting, initialization, validation, and a saved plan in a
  clean environment.
- Review the plan for public exposure, broad IAM actions, accidental secrets,
  replacement operations, backups, encryption, deletion protection, and cost.
- Apply only with explicit user approval, then verify resource health and that
  database access is limited to the intended application path.
- Run repository quality checks.

### Documentation impact

Document Terraform prerequisites, state operations, cost assumptions, and
approved apply/destroy procedures. Record plan/apply outcomes and resource
identifiers in `IMPLEMENTATION.md` without recording secrets.

### Completion condition

Terraform produces a reviewed, reproducible plan and, after explicit approval,
the applied foundation is healthy with no unplanned public or privileged path.

## Slice 5 — Initial AWS deployment

**Status:** Not started

### Outcome

The placeholder application runs on AWS in the two-container, single-task
topology defined by ADR-0003 and is reachable through TLS.

### Scope boundary

Add the task definition, ECS service with desired count one, application load
balancer, TLS routing, task roles, runtime secret injection, database migration
execution, and a repeatable manual image-publish/deploy path. Resolve the
minimum ALB-to-container routing needed by the explicit API-client design. Do
not add CI/CD automation, Cognito, retrieval, or high availability. Expose no
sensitive data or mutating product behavior before authentication exists.

### Expected artifacts

- Terraform-managed task, service, load balancer, listeners, and target groups;
- immutable image tagging and a repeatable image publish/deploy command;
- task-local UI-to-API configuration and runtime secret injection;
- a controlled migration task or equivalent pre-deployment operation;
- deployment smoke and rollback instructions.

### Verification

- Review and apply the Terraform plan only with explicit user approval.
- Verify TLS, UI reachability, UI-to-API behavior, container health, database
  readiness, logs, and absence of unintended public ports.
- Replace or restart the task and confirm ECS restores the desired count.
- Deploy a second immutable image version, then exercise the documented rollback
  to the prior version.
- Run `./scripts/quality.sh`.

### Documentation impact

Update deployment and rollback instructions and record the deployed topology,
smoke results, incidents, and compromises in `IMPLEMENTATION.md`. Update an ADR
only if the accepted topology changes.

### Completion condition

An approved, repeatable manual deployment produces one healthy ECS task with
two containers, a working TLS entry point, task-local API communication, and a
tested rollback path.

## Slice 6 — CI/CD delivery path

**Status:** Not started

### Outcome

GitHub provides deterministic quality feedback and can build, publish, and
deploy approved revisions without long-lived AWS credentials.

### Scope boundary

Extend the bootstrap GitHub configuration with container build and deployment
workflows. Use GitHub OIDC, least-privileged roles, immutable image references,
protected production environment approval, concurrency control, and pinned
actions. Infrastructure changes remain reviewed and explicitly approved. Do
not auto-merge dependency or infrastructure changes.

### Expected artifacts

- pull-request quality and container-build workflows;
- master-branch or manually dispatched publish/deploy workflow;
- Terraform plan feedback with a separately approved apply path;
- AWS OIDC provider and scoped CI/deploy roles managed by Terraform;
- deployment concurrency, provenance, failure, and rollback handling.

### Verification

- Exercise the pull-request-equivalent path and confirm formatting, linting,
  typing, tests, and image builds fail closed.
- Inspect effective GitHub and AWS permissions and confirm no stored long-lived
  AWS credential is required.
- Publish an immutable image and perform an approved deployment; verify the
  running task references the expected digest or immutable tag.
- Force a safe workflow failure and confirm production remains on the last
  healthy revision.

### Documentation impact

Document workflow triggers, required approvals, OIDC setup, and recovery.
Record live workflow and permission-test results in `IMPLEMENTATION.md`.

### Completion condition

An approved revision passes deterministic CI and follows an auditable OIDC-based
path to a verified deployment, while a failed revision leaves production
unchanged.

## Slice 7 — Cognito and internal identity foundation

**Status:** Not started

### Outcome

A user can sign in with Google through Cognito, reach the application as a
verified internal identity, and sign out without Streamlit becoming the
authorization boundary.

### Scope boundary

Resolve the token and edge-authentication flow, provision Cognito and Google
federation, add UI sign-in/session behavior, verify identity at the trusted edge
or FastAPI, and map the external subject to a stable internal identity. Add only
the persistence and authorization needed for authenticated Phase 0 access. Do
not add roles, administration, portfolio permissions, or provider access.

### Expected artifacts

- Terraform-managed Cognito resources and callback/logout configuration;
- Google OAuth secret handling outside source and Terraform state values;
- verified credential propagation through the API client;
- internal identity model, migration, repository, and narrow application
  service where required;
- authenticated and unauthenticated API/UI tests.

### Verification

- Confirm unauthenticated protected requests fail safely and cannot forge an
  identity through headers or UI state.
- Complete live Google sign-in, refresh or session continuation, and sign-out;
  verify the same external subject resolves to the same internal identity.
- Inspect logs, browser storage, task configuration, and Terraform output for
  credential leakage.
- Run automated tests and `./scripts/quality.sh`.

### Documentation impact

Update setup, callback, secret-rotation, sign-in troubleshooting, and data-flow
documentation. Record the selected flow and validation evidence in
`IMPLEMENTATION.md`; create an ADR if the flow establishes a durable new
architecture decision.

### Completion condition

The live UI completes Google-federated Cognito sign-in and sign-out, FastAPI
authorizes from verified identity, and tests demonstrate that client-controlled
identity claims are not trusted.

## Slice 8 — Operational readiness

**Status:** Not started

### Outcome

The authenticated walking skeleton is observable, recoverable within its stated
single-task limits, and safe to hand off for deterministic RAG development.

### Scope boundary

Finish structured logging and correlation, log retention, health semantics,
alarms, backup settings, deployment and migration runbooks, failure handling,
and cost visibility. Exercise representative failures and perform a final
security and operational review. Do not add redundancy, retrieval, model calls,
or production claims beyond the documented availability limits.

### Expected artifacts

- correlated structured logs and bounded error categories in CloudWatch;
- actionable task, load-balancer, and database alarms with documented owners;
- verified health checks, log retention, backups, and secret rotation paths;
- deployment, rollback, migration, incident, and recovery runbooks;
- final Phase 0 smoke checklist and known-risk record.

### Verification

- Trace one request across UI, API, database, and identity boundaries without
  exposing secrets or raw user content.
- Exercise safe task failure, database unavailability, bad configuration, and
  failed deployment scenarios; confirm health, logs, alarms, and recovery match
  the runbooks.
- Verify backup configuration, rollback, secret rotation procedure, and current
  cost estimate.
- Run all local and CI checks and complete the live authenticated smoke test.

### Documentation impact

Finalize operational runbooks, current risks, deliberate availability limits,
and `IMPLEMENTATION.md`. Update `README.md`, `DESIGN.md`, or ADRs only where
their owned truth changed.

### Completion condition

The public authenticated placeholder is healthy, observable, deployable through
the approved pipeline, recoverable through tested procedures, and ready for the
first deterministic RAG slice with all Phase 0 risks recorded.

## Stage completion criteria

Phase 0 is complete when all eight slices meet their completion conditions, the
implementation record reflects actual results and deviations, the quality and
delivery paths are green, and no unresolved issue blocks deterministic baseline
RAG work.
