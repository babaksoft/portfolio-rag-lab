# Phase 0 — Implementation Record

Add dated entries only when implementation begins. Keep results, deviations,
incidents, deliberate compromises, and follow-up work factual and link to
durable design documents rather than repeating them here.

## Results

### 2026-11-18 — Slice 1 local walking skeleton

- Added a Streamlit entry point, an explicit typed HTTP client, a FastAPI entry
  point, and the narrow `AnswerMessageService`. The returned text is visibly
  labeled as a non-factual placeholder.
- Added typed environment settings, bounded transport models and errors,
  correlation-ID propagation, and dependency-free liveness and readiness.
- Selected FastAPI and Streamlit because the durable design already requires
  those delivery adapters. Selected HTTPX for the explicit synchronous UI
  client and Pydantic Settings for typed environment loading; both integrate
  directly with FastAPI's Pydantic transport boundary without another
  abstraction layer.
- Declared Pydantic as a direct dependency because first-party production code
  imports it. Application results and UI boundary results use immutable
  Pydantic models consistently rather than mixing Pydantic with dataclasses.
- Kept `api/app.py` as a composition root and separated health and message
  routers, dependency accessors, correlation handling, and safe error
  translation into focused API modules.
- Added unit and boundary coverage for the application service, API validation
  and health, successful client serialization, backend unavailability, and an
  invalid backend response.
- `./scripts/quality.sh` passed with 8 tests. Both documented process commands
  started successfully; API liveness, API readiness, and Streamlit health
  returned successfully. A Streamlit test-harness submission crossed the real
  HTTP client and running FastAPI process and displayed the placeholder with
  its correlation identifier preserved at the API boundary.

### 2026-11-18 — Slice 2 containerized local runtime

- Added separate multi-stage API and UI images. Each installs only locked
  runtime dependencies, contains the installed application rather than a source
  bind mount, and runs as the dedicated numeric user `10001`.
- Added Compose orchestration with loopback-only published ports, dependency-
  ordered startup, image-level health checks, and a ten-second stop grace
  period. The UI reaches the API through `PORTFOLIO_RAG_UI_API_BASE_URL` at the
  Compose service address, preserving the configuration boundary intended for
  task-local ECS networking.
- Added a minimized build context and a bounded smoke command that builds and
  starts the runtime, waits for health, verifies both runtime identities, calls
  the backend through the UI-owned typed client, and stops both containers.
- Selected Debian slim Python images for compatibility with the locked Python
  dependencies and copied a version-pinned `uv` binary only into build stages;
  neither build tooling nor development dependencies are present at runtime.
- A clean local build and `uv run python scripts/container_smoke.py` passed.
  Both image
  health checks became healthy, the task-local-style client call returned the
  placeholder, both containers ran as UID `10001`, no local `.env` or build
  tool was present, and both containers stopped within the configured grace
  period.

### 2026-11-20 — Slice 3 PostgreSQL and pgvector foundation

- Selected SQLAlchemy 2 with its asynchronous engine and session support,
  asyncpg as the PostgreSQL driver, and Alembic for migration generation and
  management. Migrations live in the conventional repository-root `alembic/`
  directory and are never run implicitly at application startup.
- Added a lazy process-owned connection pool, an explicit async session factory
  for future transaction scopes, bounded connection attempts, pool disposal at
  shutdown, and secret-wrapped database URL configuration.
- Added a pinned PostgreSQL 17/pgvector 0.8.7 Compose service and a one-shot
  migration service. The API starts only after migrations succeed, while host
  ports remain loopback-only and overrideable for isolated runs.
- Added the initial reversible migration, which enables only the `vector`
  extension. No application tables, mapped persistence models, repositories,
  embedding dimensions, or indexes were introduced ahead of their use cases.
- Readiness now performs a safe, bounded database query and returns HTTP 503
  without infrastructure detail when PostgreSQL is unavailable. Liveness
  remains dependency-free.
- A fresh isolated Compose database migrated successfully and exposed the
  pgvector extension. The final pinned image reported PostgreSQL 17.12 and
  pgvector 0.8.7. The integration test passed; downgrade removed the extension,
  and reapplying migrations restored it. With PostgreSQL stopped, readiness
  returned 503 while liveness returned 200; readiness recovered to 200 after
  restart.

### 2026-11-20 — Slice 4 Terraform-managed AWS foundation

- Added a protected local-state bootstrap for an encrypted, versioned,
  public-access-blocked S3 backend using Terraform's native S3 lockfile. The
  production configuration has explicit backend configuration rather than
  embedding an account-specific bucket name.
- Added a two-Availability-Zone VPC with public edge, private application, and
  isolated database subnets. One NAT gateway serves both application subnets as
  a deliberate Phase 0 cost/availability tradeoff; database subnets have no
  internet route.
- Added directional security-group rules for the future edge, application, and
  database boundaries. Public ingress is limited to HTTPS on the unused edge
  group, Streamlit ingress is edge-only, PostgreSQL ingress is application-only,
  and no network path exposes the API port.
- Added immutable, scan-on-push ECR repositories with bounded retention, an ECS
  cluster with Fargate capacity providers, 30-day API/UI log groups, and separate
  least-privileged execution and application task roles. No task definition,
  service, load balancer, Cognito resource, or delivery role was introduced.
- Added a private, encrypted, single-AZ PostgreSQL 17 RDS instance with seven-day
  backups, final snapshots, deletion protection, storage autoscaling, and an
  RDS-managed master credential in Secrets Manager. The second application
  secret is an empty container; Terraform manages no secret payload.
- Added explicit registered-domain and application-hostname inputs, a public
  Route 53 zone, DNS-validated ACM certificate, and registrar-delegation
  procedure. No hostname was inferred from the AWS account.
- Selected Terraform 1.10 or newer for S3 native lockfiles and constrained the
  AWS provider to major version 6. Provider 6.73.0 was locked and both bootstrap
  and production configurations passed `terraform validate` after clean
  initialization.
- Selected `us-east-1` as the explicit production and state home region rather
  than inheriting an operator's CLI default. The runbook supports AWS CLI v2 IAM
  Identity Center profiles through the standard credential chain without
  coupling Terraform to a personal profile or blocking later OIDC credentials.
- Selected `babaksoft.dev` as the public zone and
  `portfolio-rag.babaksoft.dev` as this application's hostname. Added a
  version-controlled Terraform operator policy plus protected operator and ECS
  task boundaries. Project roles require the ECS boundary and may be passed
  only to ECS tasks; the operator cannot modify either boundary or create and
  delete hosted zones. Account, region, state, hostname, and hosted-zone values
  are rendered from Terraform inputs rather than duplicated as literals in the
  policy documents.
- On 2026-11-21, an explicitly approved bootstrap plan was applied to AWS
  account `509399640122` in `us-east-1`: eight resources were added with no
  changes or destruction. It created the encrypted, versioned, non-public state
  bucket `portfolio-rag-lab-tfstate-509399640122-us-east-1` and the protected
  `PortfolioRagTerraformOperatorBoundary` and `PortfolioRagEcsTaskBoundary`
  policies under `/portfolio-rag/`. A post-apply refresh reported no drift.
- Attached the reviewed inline policy and customer-managed boundary to the
  two-hour `PortfolioRagTerraformOperator` IAM Identity Center permission set,
  assigned it to the existing user in account `509399640122`, and successfully
  provisioned it. Configured an independent `portfolio-rag` AWS CLI profile and
  SSO session. The profile resolved to the generated restricted role, could
  read the configured state bucket location, and was denied unrelated
  `iam:ListUsers` access as expected.
- Initialized the production S3 backend with native locking through the
  restricted operator and produced a saved production plan. The plan contains
  46 creates, no changes or destruction, and no unexpected action type. Review
  confirmed private encrypted deletion-protected RDS, no automatic public IPs,
  public ingress only on the future edge group's TCP 443 rule, bounded ECS
  roles, and no configured secret payload.
- Estimated fixed baseline charges at approximately USD 51.78 per 730-hour
  month before usage-dependent charges: one NAT gateway, one public IPv4
  address, single-AZ `db.t4g.micro`, 20 GiB gp3 RDS storage, two Secrets Manager
  secrets, and one Route 53 hosted zone. Current AWS prices were checked during
  review; traffic, logs, image storage, DNS queries, excess backups, and NAT
  data processing remain variable.
- Route 53 registration of `babaksoft.dev` completed successfully. The domain
  is active with auto-renewal and contact privacy enabled, and registration
  created public hosted zone `Z06495321W44G2MBDFW2H`. The zone was imported
  into the production S3 state through the restricted operator and protected
  with `prevent_destroy`; no DNS record or name-server mutation occurred.
- Replaced fixed IAM policy JSON with Terraform-rendered templates. The exact
  rendered operator and ECS boundary documents passed AWS Access Analyzer with
  zero findings. An approved bootstrap plan updated only the operator boundary
  in place (zero creates or destroys), narrowing DNS writes to the imported
  hosted zone and allowing tags only on that zone. The matching Identity Center
  inline policy was updated and reprovisioned successfully, and a subsequent
  bootstrap refresh reported no drift.
- Corrected route-table-association and ACM-validation instance keys so imports
  and fresh plans do not depend on apply-time resource objects. The registrar's
  hosted-zone comment is preserved explicitly; the production plan changes
  only the zone's standard project tags while retaining its ID, domain, and
  four authoritative name servers.
- Produced and machine-reviewed the post-registration production saved plan:
  45 creates, one in-place hosted-zone tag update, and zero destroys. Review
  reconfirmed that RDS is private, encrypted, deletion-protected, uses an
  RDS-managed password and final snapshots; no subnet assigns public IPs; the
  only public ingress is TCP 443 on the future edge group; and both ECS roles
  retain the bootstrap-managed permissions boundary.
- Applied the explicitly approved production plan. The first apply created 43
  of 45 planned resources, including the VPC, NAT gateway, ECR repositories,
  ECS cluster, IAM roles, log groups, Route 53 validation record, and issued ACM
  certificate. RDS creation initially failed because the operator lacked the
  AWS-documented `kms:DescribeKey` permission required for an RDS-managed master
  password using the default Secrets Manager key.
- Added only `kms:DescribeKey`, restricted to keys in the production account and
  region carrying `alias/aws/secretsmanager`. The rendered policy passed AWS
  Access Analyzer with zero findings; an approved bootstrap plan updated the
  boundary in place, and the Identity Center permission set reprovisioned
  successfully. The restricted profile then described that AWS-managed key but
  received no decrypt, data-key, grant, or key-management permission.
- A refreshed convergence plan contained only the two unfinished resources:
  the RDS instance and its dependent ECS execution-role policy (`2` creates,
  no changes or destroys). Applying it completed the foundation. Post-apply
  checks found RDS `available`, private, encrypted, deletion-protected, and
  backed by an active RDS-managed secret; ACM `ISSUED`; ECS `ACTIVE` with no
  running tasks; and the NAT gateway `available`. A full production refresh
  reported no drift.

### 2026-11-21 — Slice 5 initial AWS deployment

- Added the Terraform-managed public Application Load Balancer, TLS listener,
  alias record, Streamlit target group, two-container application task,
  one-count ECS service, and controlled one-off migration task. Only TCP 443 is
  public; the load balancer reaches only Streamlit on TCP 8501, and the UI
  reaches FastAPI over the shared task-local loopback interface.
- Configured ECS deployment rollback, container health dependencies, private
  task networking, no public task IP, and RDS-backed API readiness. The RDS
  managed secret remains the only database credential source: ECS injects its
  username and password JSON fields, while the API safely assembles the
  SQLAlchemy URL without copying credentials into Terraform state.
- Added commands for publishing immutable API and UI image tags and running a
  migration task whose exit code is checked before service deployment. Added a
  staged first-deployment procedure, smoke checklist, task-restoration test,
  second-version deployment, and rollback procedure to the Terraform runbook.
- Expanded the bootstrap-managed Terraform operator boundary only for the ECS
  task/service, migration/recovery task, repository-scoped image publication,
  and Elastic Load Balancing operations introduced by this slice. AWS Access
  Analyzer reported zero findings for the rendered policy.
- Applied the explicitly approved operator-boundary update in place and
  reprovisioned the matching Identity Center permission set. The staged
  zero-task production plan contained seven creates, no changes, and no
  destroys; applying it created the task definitions, service, load balancer,
  TLS listener, target group, and DNS alias without starting application
  traffic.
- Published and deployed immutable `slice5-20261121-2beab6c970fb-v2` images
  after upgrading both exact runtime base-image pins to Python 3.12.16. ECR
  reported no critical findings; the API digest is
  `sha256:ac4522cd5fa78841a3807c1ac718403ca1f1770652f6397913e6ee9a7f89eba2`
  and the UI digest is
  `sha256:e76a42c2535ff20f21ace563e39114879ed2627e1aade9bb06a646a525249111`.
- The private migration task exited zero and applied the pgvector migration.
  The activation plan changed only desired count from zero to one. TLS health,
  the healthy ALB target, one healthy two-container task, repeated
  database-backed API readiness probes, exact image digests, private task ENI,
  and effective directional security-group rules all matched the design.
  A private one-off task exercised the real UI API client over task-local
  loopback and both containers exited zero.
- Stopping the sole service task caused the expected brief outage; ECS restored
  a different healthy task and returned to one running and one desired. A
  second immutable `v3` tag deployed successfully, after which the documented
  rollback restored `v2` on task-definition revision 3. Final TLS, container,
  service, and target health checks passed, and a production refresh reported
  no drift. A manual browser submission at the live entry point
  `https://portfolio-rag.babaksoft.dev` displayed the expected explicitly
  non-factual placeholder response.
- `./scripts/quality.sh` passed with 11 tests and one opt-in database integration
  test skipped because its external URL was not configured.
  `./scripts/terraform_quality.sh`, shell syntax checks, and
  `git diff --check` also passed.

### 2026-11-21 — Slice 6 CI/CD delivery path

- Added pull-request and `master` container builds alongside the existing
  deterministic Python quality workflow. Both production Dockerfiles fail
  closed in hosted feedback before their images can reach delivery.
- Added a manually dispatched, serialized production workflow that accepts only
  revisions reachable from `master`, publishes immutable full-commit image
  tags, records their digests, and transfers a saved Terraform plan to a
  separately approved `production` environment job.
- Restricted the automated plan to the two ECS task-definition replacements
  and one ECS service update. Any infrastructure change fails the workflow and
  remains on the explicit manual plan/apply path.
- Added Terraform-managed GitHub OIDC trust roles with separate read-only
  planning, repository-scoped ECR publishing, and protected-environment
  deployment permissions. Trust policies bind the `sts.amazonaws.com` audience
  and exact repository subject; no long-lived AWS credential is required.
- Added pre-deployment migration registration, running-digest verification, and
  best-effort restoration of the prior healthy ECS task definition when apply
  or verification fails. Migrations remain backward-compatible and are not
  automatically reversed.
- The live provision, deploy, rollback, and teardown cycle was subsequently
  verified and working. This closes the live activation and failure-path work
  that remained pending when the implementation was first prepared.

### 2026-11-22 — Slice 7 Cognito and internal identity foundation prepared

- Selected the dual-verification flow in
  [ADR-0004](../../adr/0004-verify-alb-and-cognito-credentials-in-api.md): the
  ALB authenticates the browser, while FastAPI verifies both the ALB-signed
  claims and Cognito-signed access token, requires matching subjects, and
  authorizes only the `reviewers` group.
- Added Terraform-managed Cognito user pool, managed-login domain, `reviewers`
  group, app client, ALB authentication action, and a narrow unauthenticated
  logout route. Google federation is reconciled during apply by reading its
  secret directly from the existing application secret; the Google secret is
  absent from Terraform configuration, plan values, and state.
- Added a reversible identity-table migration, natural domain values, repository
  protocol, PostgreSQL adapter, and the narrow `ResolveIdentityService`. An
  atomic subject upsert preserves the application-owned UUID across sessions
  and refreshes only the optional verified email.
- Streamlit forwards the two credentials only over task-local HTTP. FastAPI
  fetches signing keys from fixed regional AWS endpoints, validates signer,
  issuer, client, use, expiry, subject, and group, and returns bounded 401/403
  failures without credential diagnostics.
- Added isolated cryptographic, API-boundary, client-propagation, settings, and
  optional database-integration coverage. `./scripts/quality.sh` passed with 20
  tests and the opt-in database test skipped; that test then passed twice
  against an isolated PostgreSQL/pgvector container, before and after a clean
  identity-migration downgrade/reapply cycle. Terraform formatting and
  validation, shell syntax, and `git diff --check` passed. Live Google client
  creation, secret population, approved Terraform apply, reviewer assignment,
  browser sign-in, session continuation, sign-out, leakage inspection, and
  stable-identity smoke checks remain pending explicit live approval.

### 2026-11-24 — Slice 7 live activation verified

- Activated Google federation and verified reviewer sign-in, stable internal
  identity resolution, one protected placeholder exchange, same-tab sign-out
  to `/signed-out`, sign-in again, and a second protected exchange with
  application revision `dfa93e0128102bf181ac48a53df8ecd34867d954`.
- Accepted Google session reuse after application sign-out as expected OAuth
  behavior; Slice 7 does not promise Google account selection or global Google
  logout. Deferred proactive stale-tab synchronization and automatic expiry
  navigation until the UI has meaningful authenticated state. FastAPI still
  verifies token expiry on every protected operation and returns a bounded 401.
- Made the production root deliberately disposable between infrequent live
  test windows. Provider deletion protection and Terraform `prevent_destroy`
  guards remain disabled for RDS, ALB, Cognito, and the hosted zone; the remote
  state bucket and bootstrap IAM boundaries remain protected. This accepts
  lengthy staged reconstruction, Cognito user recreation, and Route 53
  redelegation in exchange for avoiding idle infrastructure cost.

### 2026-11-24 — Slice 8 operational readiness prepared locally

- Added bounded JSON application logging with stable event names, service and
  severity fields, request latency and outcome metadata, safe correlation
  propagation, and explicit authentication, authorization, identity, database,
  client, and unexpected-failure categories. Raw user content, credentials,
  identity attributes, and exception details are excluded by construction.
- Added Terraform-managed SNS routing and actionable ECS, load-balancer, and
  RDS alarms, including database lifecycle events. Alarm descriptions name the
  repository owner and point to the incident procedure; email delivery remains
  optional and requires subscription confirmation. Expanded the bootstrap
  operator boundary only for those CloudWatch, SNS, and RDS event-subscription
  lifecycles and added matching read access to the GitHub planning role; the
  rendered operator policy remains below IAM's managed-policy size quota.
- Made CloudWatch retention explicit and bounded while retaining the existing
  seven-day automated RDS backup, final-snapshot, health-check, deployment
  rollback, and separate migration controls.
- Added the operational readiness runbook covering health semantics,
  correlation queries, alarm triage, representative failure drills, backup and
  restore evidence, migration and rotation paths, current-cost review, the
  final smoke checklist, and accepted single-task risks.
- `./scripts/quality.sh` passed with 31 tests and the opt-in database integration
  test skipped because its isolated URL was not configured. Terraform formatting
  and validation for both roots, shell syntax, rendered-policy JSON validation,
  the IAM managed-policy size check, and `git diff --check` also passed. Live
  alarm transitions, failure drills, isolated backup restore, rotation checks,
  current cost evidence, leakage review, and the complete authenticated smoke
  test remain pending an explicitly approved active window.

### 2026-11-26 — Architecture refinement step 1

- Moved API dependency construction and database shutdown into
  `portfolio_rag.composition`. The HTTP adapter registers routes, middleware,
  and error handlers with the supplied dependencies. The app factory still
  accepts settings, readiness, credential verification, and identity
  resolution overrides.
- Updated the README and API image to launch
  `portfolio_rag.composition.asgi:app`. The runtime and Alembic share database
  URL resolution in composition.
- All 14 API tests passed. `./scripts/quality.sh` passed with 31 tests and the
  opt-in database integration test skipped because its isolated URL was
  unset. A fresh Python process confirmed that importing `portfolio_rag.api`
  neither constructs the app nor loads the database adapters. Alembic
  generated offline migration SQL, and `git diff --check` passed.
- `uv run python scripts/container_smoke.py` passed with an isolated Compose
  project. PostgreSQL migrations ran, the UI reached the API over HTTP, and
  shutdown completed in 1.8 seconds.

## Deviations

None.

## Incidents

- The first Slice 5 boundary apply was rejected before changing AWS because the
  rendered managed policy exceeded IAM's 6,144-character quota. Removing
  optional `Sid` labels reduced it to 5,835 non-whitespace characters without
  changing permissions. AWS Access Analyzer returned zero findings and the
  corrected one-resource plan applied successfully.
- The first image-publish attempt inherited an unrelated `AWS_REGION` value and
  targeted `eu-west-3`; ECR denied the upload before any image was pushed. Both
  deployment scripts now use the project-specific
  `PORTFOLIO_RAG_AWS_REGION`, defaulting to the selected `us-east-1` home
  region.
- The first published `v1` images were blocked before deployment because ECR
  reported 12 critical findings in the Python 3.12.8 Debian base layer. The
  exact base pin was upgraded to Python 3.12.16 and replacement `v2` scans
  completed with no critical findings. The undeployed `v1` images remain in
  immutable ECR history and will age out under the 20-image lifecycle policy.

- The first production apply partially completed before RDS returned
  `KMSKeyNotAccessibleFault`. Terraform released its state lock and retained all
  successfully created resources in remote state. Root cause was a missing
  documented prerequisite permission, not an inaccessible or disabled key.
  The least-privilege policy correction and two-resource convergence plan are
  recorded above; no resource was deleted or replaced during recovery.

## Deliberate compromises

- The UI shows only the current exchange; durable conversation identity and
  history remain deferred until a use case requires them.
- Application sign-out does not terminate the upstream Google session or
  proactively invalidate already-open Streamlit tabs. Existing credentials are
  rejected when they expire; cross-tab synchronization is deferred until the
  application has meaningful authenticated state.
- The production application root is destroyed between infrequent live test
  windows. Its deletion guards remain disabled, while durable Terraform state
  and bootstrap IAM controls stay protected. Provisioning is a staged manual
  operation because DNS delegation and Google secret population require human
  input.
- The AWS provider's Cognito identity-provider resource stores Google provider
  details in Terraform state. A secret-safe, idempotent apply-time reconciler
  therefore manages that one provider binding while Terraform owns the user
  pool, domain, group, app client, and its reconciliation lifecycle trigger.

## Follow-up work

- Review and prioritize the 15 high, 25 medium, and 6 low findings remaining in
  each deployed image scan. They did not cross the documented critical-finding
  deployment gate but remain explicit dependency/base-image maintenance work.

- When image build time becomes material in CI or deployment, separate the
  locked third-party dependency layer from the first-party package install and
  add a BuildKit cache mount for uv downloads. Docker's standard layer cache is
  sufficient for the intentionally small walking skeleton, so that complexity
  is deferred until measurements justify it.
