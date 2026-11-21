# AWS foundation

This directory owns the Terraform-managed Phase 0 AWS foundation and initial
manual deployment. It does not create Cognito resources or a CI/CD delivery
workflow; those belong to later slices.

## Prerequisites and inputs

Install Terraform 1.10 or newer (but earlier than 2.0) and AWS CLI v2. Use an
AWS identity authorized to manage only the resources in the reviewed plan.
The selected production home region is `us-east-1`; both Terraform roots set it
explicitly instead of inheriting a developer's AWS CLI default. Changing regions
after resources exist is a migration and requires a separately reviewed plan.

### IAM Identity Center authentication

Terraform's AWS provider and S3 backend both use the standard AWS credential
chain, including AWS CLI v2 IAM Identity Center profiles. Keep the profile and
SSO session configuration in the user-level AWS config, never in this
repository. Log in, select the profile for the current shell, and confirm both
the account and caller before any plan or apply:

```sh
export AWS_PROFILE=portfolio-rag
aws sso login --profile "$AWS_PROFILE"
aws sts get-caller-identity --profile "$AWS_PROFILE"
aws configure get region --profile "$AWS_PROFILE"
```

The profile's configured region may differ because Terraform passes
`us-east-1` explicitly. Do not set `profile` in provider or backend files: that
would couple shared infrastructure to one operator and would conflict with the
OIDC role credentials planned for CI/CD. An expired SSO session is repaired by
running `aws sso login` again; do not create long-lived access keys as a
workaround.

Use a dedicated infrastructure permission set where practical. Its effective
permissions must cover only the reviewed state and foundation operations. A
broad administrator-style permission set can bootstrap the first narrowly
scoped roles, but its use should be time-bounded and recorded rather than
treated as the normal Terraform identity.

The selected public domain is `babaksoft.dev`, and this application's hostname
is `portfolio-rag.babaksoft.dev`. Route 53 registration created the public zone;
Terraform adopts that zone by import and protects it from destruction. A
different account must supply its own registered domain and hosted-zone ID.

Example files contain safe project defaults and account-specific resource names
that a new operator must review and replace. Never put credentials, database
passwords, or secret payloads in `.tfvars`, backend files, CLI arguments, or
committed files. RDS generates its master credential directly in Secrets
Manager, so the password does not enter Terraform configuration or outputs.

## Bootstrap remote state

The state bucket is intentionally a separate local-state configuration because
an S3 backend cannot create its own bucket. The bootstrap also owns two
protected customer-managed IAM boundaries: one caps the Terraform operator and
one is mandatory on every ECS execution or task role. The production operator
cannot modify either guardrail.

Copy `bootstrap/terraform.tfvars.example` to an ignored `.tfvars` file, review
the bootstrap plan, and apply it with the temporary administrative SSO profile
only after explicit approval:

```sh
export PORTFOLIO_RAG_BOOTSTRAP_PROFILE=your-administrative-sso-profile
aws sso login --profile "$PORTFOLIO_RAG_BOOTSTRAP_PROFILE"
export AWS_PROFILE="$PORTFOLIO_RAG_BOOTSTRAP_PROFILE"
aws sts get-caller-identity --profile "$AWS_PROFILE"

terraform -chdir=terraform/bootstrap init
terraform -chdir=terraform/bootstrap fmt -check
terraform -chdir=terraform/bootstrap validate
terraform -chdir=terraform/bootstrap plan -out=bootstrap.tfplan
terraform -chdir=terraform/bootstrap show bootstrap.tfplan
terraform -chdir=terraform/bootstrap apply bootstrap.tfplan
```

The bucket blocks public access, rejects non-TLS requests, encrypts objects,
versions state, and has Terraform destruction protection. Keep the bootstrap
state in a protected operator location; it contains no application secrets but
is required to manage the bucket.

### Configure the Terraform operator permission set

The version-controlled operator policy template is
`bootstrap/policies/portfolio-rag-terraform-operator.json.tftpl`. Terraform
renders account, region, state, hostname, and exact hosted-zone values into both
the customer-managed boundary and an output for the permission set's inline
grant. Run the following commands from the repository root only after the
bootstrap has created the boundary and after setting `INSTANCE_ARN` and
`PERMISSION_SET_ARN` to the reviewed IAM Identity Center resources. The
bootstrap profile name is an operator-local input; the repository neither
requires nor assumes any particular name:

```sh
terraform -chdir=terraform/bootstrap output -raw \
  terraform_operator_policy_json \
  > /tmp/portfolio-rag-terraform-operator.json

aws sso-admin put-inline-policy-to-permission-set \
  --profile "$PORTFOLIO_RAG_BOOTSTRAP_PROFILE" \
  --region us-east-1 \
  --instance-arn "$INSTANCE_ARN" \
  --permission-set-arn "$PERMISSION_SET_ARN" \
  --inline-policy file:///tmp/portfolio-rag-terraform-operator.json

aws sso-admin put-permissions-boundary-to-permission-set \
  --profile "$PORTFOLIO_RAG_BOOTSTRAP_PROFILE" \
  --region us-east-1 \
  --instance-arn "$INSTANCE_ARN" \
  --permission-set-arn "$PERMISSION_SET_ARN" \
  --permissions-boundary \
    '{"CustomerManagedPolicyReference":{"Name":"PortfolioRagTerraformOperatorBoundary","Path":"/portfolio-rag/"}}'
```

After assigning the permission set, provision changes to account
`509399640122`, authenticate the `portfolio-rag` profile, and verify its caller:

```sh
aws sso-admin provision-permission-set \
  --profile "$PORTFOLIO_RAG_BOOTSTRAP_PROFILE" \
  --region us-east-1 \
  --instance-arn "$INSTANCE_ARN" \
  --permission-set-arn "$PERMISSION_SET_ARN" \
  --target-type AWS_ACCOUNT \
  --target-id 509399640122

export AWS_PROFILE=portfolio-rag
aws sso login --profile "$AWS_PROFILE"
aws sts get-caller-identity --profile "$AWS_PROFILE"
```

The operator can create project-prefixed roles only when the bootstrap-managed
ECS boundary is attached, and it can pass those roles only to ECS tasks. Its
certificate requests and DNS record changes are limited to the selected
`babaksoft.dev` names. Regional write operations are limited to `us-east-1`.
Its only KMS permission is `DescribeKey`, restricted by the
`alias/aws/secretsmanager` resource alias; RDS requires this read operation when
it creates and manages the database master-password secret.
Some VPC operations cannot be narrowed to not-yet-created resource identifiers;
the remaining exposure is therefore the enumerated network actions in that one
region, not general EC2 or account administration.

Copy `production/backend.hcl.example` to `production/backend.hcl`, use the
bucket output, and initialize with S3 native locking:

```sh
terraform -chdir=terraform/production init -backend-config=backend.hcl
```

The backend uses an S3 `.tflock` object. Terraform acquires it for state-writing
operations and releases it on completion. Do not use `force-unlock` until the
owning operation is confirmed dead; record and peer-review any forced unlock.
State recovery uses a known-good S3 object version, copied back only during a
documented incident with all Terraform writers stopped.

## Plan and apply

Copy `production/terraform.tfvars.example` to an ignored environment-specific
`.tfvars` file and review its selected domain, hostname, and boundary ARN. Run
the local structural checks, then create a saved plan:

```sh
./scripts/terraform_quality.sh
terraform -chdir=terraform/production plan \
  -var-file=production.tfvars \
  -out=foundation.tfplan
terraform -chdir=terraform/production show foundation.tfplan
```

Before approval, verify the account and region and review:

- only the application load balancer is publicly reachable, on TCP 443; no
  task, database, or secret has a public network path;
- the edge group forwards only to Streamlit on TCP 8501 and does not expose the
  FastAPI port;
- application ingress is edge-group to TCP 8501 and database ingress is
  application-group to TCP 5432;
- IAM has no broad action except the resource-independent ECR authorization
  token call, and secret access names only the two runtime secrets;
- RDS is encrypted, single-AZ, backed up for seven days, deletion-protected,
  and will take a final snapshot;
- no secret values appear in configuration, outputs, or the plan;
- the plan has no unexpected replacement or destruction.

The expected production region is `us-east-1`. Do not approve a plan whose
provider or backend resolves to another region, even if the active CLI profile
defaults elsewhere.

The Terraform operator deliberately cannot create or delete hosted zones. After
Route 53 registration creates the zone, put its ID in the reviewed bootstrap
inputs, apply the resulting boundary update, reprovision the Identity Center
permission set, and import the zone with the restricted operator before the
first production plan:

```sh
terraform -chdir=terraform/production import \
  -var-file=terraform.tfvars \
  aws_route53_zone.main YOUR_HOSTED_ZONE_ID
```

The import changes Terraform state, not the live DNS records. Confirm the next
saved plan preserves the imported zone ID, registrar comment, and name servers;
only the standard project tags should change on that zone. ACM validation then
uses a record within the already delegated zone.

Apply only the exact reviewed plan after explicit approval:

```sh
terraform -chdir=terraform/production apply foundation.tfplan
```

Afterward, confirm ACM reports `ISSUED`, RDS reports `available` and is not
public, and the route tables and effective security-group rules match the plan.
The application secret remains empty until a later slice defines a concrete
secret contract. Database credentials come directly from the RDS-managed
secret and must not be copied into it.

## Publish and deploy the application

The API and UI repositories reject mutable tag overwrites. Choose a unique tag,
normally the full source revision, authenticate the restricted AWS profile, and
publish both images:

```sh
export AWS_PROFILE=portfolio-rag
aws sso login --profile "$AWS_PROFILE"
./scripts/aws_publish_images.sh "$(git rev-parse HEAD)"
```

Put that exact tag in both `api_image_tag` and `ui_image_tag` in the ignored
`production.tfvars`. Never use `latest`. Review ECR scan findings before
deploying; a critical finding blocks deployment until it is understood and
resolved.

The first deployment is deliberately staged so the ECS service cannot accept
traffic before the database migration succeeds:

1. Update and apply the bootstrap root first, using the administrative profile
   and the explicit approval process above. Reprovision the restricted
   permission set so its expanded ECS and load-balancer permissions take
   effect.
2. Create and review a production saved plan with
   `-var=service_desired_count=0`. Apply that exact plan only after approval.
   This creates the load balancer and task definitions while holding the
   service at zero tasks.
3. Run `./scripts/aws_run_migration.sh`. It starts the private one-off Fargate
   migration task, waits for it to stop, and fails unless Alembic exits zero.
4. Create a new saved plan from the normal inputs (desired count defaults to
   one), confirm the only expected service change is `0 -> 1`, and apply that
   exact plan only after approval.

For later deployments, publish a new immutable tag, update both image-tag
inputs, review the saved production plan, run the migration command, and then
apply the exact approved plan. Alembic revisions must remain backward-compatible
with the currently running task because the migration precedes replacement.
The ECS deployment circuit breaker rolls back a task that does not become
healthy, but it cannot undo a database migration.

### Deployment smoke test

After ECS reaches steady state, perform all of these checks:

```sh
curl --fail --silent --show-error \
  "https://portfolio-rag.babaksoft.dev/_stcore/health"
aws ecs describe-services \
  --region us-east-1 \
  --cluster portfolio-rag-production \
  --services portfolio-rag-production
aws logs tail /ecs/portfolio-rag-production/api --region us-east-1 --since 10m
aws logs tail /ecs/portfolio-rag-production/ui --region us-east-1 --since 10m
```

Open `https://portfolio-rag.babaksoft.dev`, submit a message, and confirm the
explicit placeholder response appears. Confirm the service reports one running
and one desired task, the target group reports one healthy target, API logs show
successful readiness checks, neither log stream contains a database password,
and the task has no public IP. Inspect the effective security groups: public
ingress must be only edge TCP 443, edge-to-task traffic only TCP 8501, and
task-to-database traffic only TCP 5432.

To test desired-count recovery, stop the current task with `aws ecs stop-task`,
then wait for the service to return to one healthy running task. This is an
intentional brief outage in the Phase 0 single-task topology and requires
explicit approval before running against the live environment.

### Rollback

Keep the prior immutable API and UI tags. To exercise rollback after deploying
a second version, restore both prior tags in `production.tfvars`, create and
review a saved plan, and apply that exact plan after approval. Wait for steady
state and repeat the complete smoke test. Do not attempt application rollback
when a non-backward-compatible migration has run; use the migration recovery
procedure appropriate to that reviewed revision first.

## Cost and recovery assumptions

The default deliberately trades availability for Phase 0 cost: one NAT gateway,
one `db.t4g.micro` single-AZ RDS instance, 20 GiB gp3 storage with autoscaling to
100 GiB, one public Application Load Balancer, and one continuously desired
0.5-vCPU/1-GiB Fargate task after deployment. NAT hourly/data processing, RDS,
Fargate, load-balancer capacity, Route 53, CloudWatch ingestion/storage, ECR
storage, public IPv4, and data transfer can incur charges even when the
application is idle. Confirm current regional pricing with the AWS Pricing
Calculator before approval. Container Insights is enabled for operational
visibility and can add CloudWatch cost.

The single NAT gateway is an Availability Zone dependency, and the database has
no standby. RDS backups and a final snapshot improve recoverability but do not
provide high availability. ECR retains only the newest 20 images; CloudWatch
logs retain 30 days.

For an approved teardown, first retain required state, database snapshots, and
image references. Change `database_deletion_protection` to false and remove the
database `prevent_destroy` lifecycle guard in a separately reviewed change.
Review a saved destroy plan before running it. The state bucket has its own
`prevent_destroy` guard and must remain until all managed infrastructure and
state retention obligations are resolved. Never bypass either guard ad hoc.
