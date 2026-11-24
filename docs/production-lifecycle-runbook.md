# Production lifecycle runbook

This runbook is the terminal-first recovery path for the Phase 0 production
environment. Use it when an interactive coding session is unavailable or low
on usage credit. It covers manual reconstruction, activation, smoke testing,
rollback, suspension, and full teardown.

The Google OAuth flow was verified on 2026-11-24 with application revision
`dfa93e0128102bf181ac48a53df8ecd34867d954`. A complete verification includes
Google sign-in, one placeholder message, same-tab sign-out to `/signed-out`,
sign-in again, and a second placeholder message.

## Safety boundary

- Run commands from the repository root unless a command says otherwise.
- Use `us-east-1` and AWS account `509399640122` only.
- Check the active AWS identity before every apply or service mutation.
- Use immutable `sha-<full-commit>` image tags; never use `latest`.
- Review saved plans before applying them.
- Never apply an old saved plan after another deployment or state change.
- Do not use targeted Terraform destroy, delete Terraform state entries, or
  manually delete Terraform-managed resources. Use the complete reviewed
  destroy plan when entering the cold state.
- Database migrations must remain backward-compatible with the running and
  rollback application revisions. Do not automatically downgrade the database.

Set the common shell values:

```sh
export AWS_REGION=us-east-1
export PORTFOLIO_RAG_CLUSTER=portfolio-rag-production
export PORTFOLIO_RAG_SERVICE=portfolio-rag-production
export PORTFOLIO_RAG_DATABASE=portfolio-rag-production
export PORTFOLIO_RAG_STABLE_SHA=dfa93e0128102bf181ac48a53df8ecd34867d954
export PORTFOLIO_RAG_STABLE_TAG="sha-$PORTFOLIO_RAG_STABLE_SHA"

aws sts get-caller-identity --region "$AWS_REGION"
git status --short --branch
git fetch origin
git merge-base --is-ancestor "$PORTFOLIO_RAG_STABLE_SHA" origin/master
```

Change `PORTFOLIO_RAG_STABLE_SHA` after a later revision passes the complete
production smoke test.

## Operating states

The current Terraform root supports three safe operating states:

| State | ECS desired count | RDS | ALB and NAT | Purpose |
| --- | ---: | --- | --- | --- |
| Active | 1 | available | present | Deployment and live testing |
| Suspended | 0 | stopped | present | Short idle period |
| Cold | absent | absent | absent | Longer idle period and minimum running cost |

Suspension stops Fargate and RDS instance-hour charges. RDS storage and backup
charges continue. The public ALB, NAT gateway, and their public IPv4 addresses
also remain billable. Prefer a complete manual teardown for longer idle periods.
The cold state deliberately retains only separately bootstrapped Terraform
state and IAM controls, retained snapshots and images, the registered domain,
and external Google OAuth credentials.

AWS restarts a stopped RDS instance after at most seven consecutive days.
During a longer pause, check it regularly and stop it again if it becomes
`available`. See the [AWS RDS stop/start documentation][rds-stop].

[rds-stop]: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_StopInstance.html

## Reconstruct production from the cold state

Reconstruction is intentionally manual and staged because DNS delegation and
the Google client secret cannot be completed safely by one unattended apply.
Saved plans are state-specific: never pre-generate later stages before the
earlier stage has been applied.

1. Run `./scripts/quality.sh` and `./scripts/terraform_quality.sh` on the exact
   revision being provisioned.
2. Set `AWS_REGION=us-east-1`, authenticate an approved AWS identity, and verify
   account `509399640122` with `aws sts get-caller-identity`.
3. Review the ignored `terraform/production/backend.hcl` and
   `terraform/production/terraform.tfvars`; ensure both image tags name already
   published immutable images.
4. Initialize the production root and create the first saved plan:

   ```sh
   terraform -chdir=terraform/production init -backend-config=backend.hcl
   terraform -chdir=terraform/production plan \
     -input=false \
     -var-file=terraform.tfvars \
     -var=service_desired_count=0 \
     -target=aws_route53_zone.main \
     -out=reconstruct-zone.tfplan
   terraform -chdir=terraform/production show reconstruct-zone.tfplan
   ```

5. Apply only that zone plan with an identity authorized to create hosted
   zones. Copy the new zone's four name servers to the `babaksoft.dev`
   registration and wait until public DNS reports the new delegation. A
   recreated zone never reuses the deleted zone's name servers.
6. Create and review a saved plan targeting only
   `aws_secretsmanager_secret.application`, apply it, and interactively set its
   JSON value to `google_oauth_client_secret` without writing that value to a
   plan, variable, repository file, or shell history. Each reconstruction uses
   a timestamped secret name, so a prior secret in its recovery window does not
   block this stage. After applying it, obtain the new ARN with
   `terraform -chdir=terraform/production output -raw application_secret_arn`.
7. Generate `reconstruct-foundation.tfplan` with desired count zero, review all
   creates and sensitive boundaries, and apply it. This stage can take more
   than 30 minutes for RDS, NAT, ACM, and Cognito readiness.
8. Run the database migration task, create a fresh activation plan changing
   only ECS desired count from zero to one, apply it, restore the approved user
   to the Cognito `reviewers` group, and run the complete smoke test.

The commands for stages 6 and 7 are:

```sh
terraform -chdir=terraform/production plan \
  -input=false \
  -var-file=terraform.tfvars \
  -var=service_desired_count=0 \
  -target=aws_secretsmanager_secret.application \
  -out=reconstruct-secret.tfplan

terraform -chdir=terraform/production plan \
  -input=false \
  -var-file=terraform.tfvars \
  -var=service_desired_count=0 \
  -out=reconstruct-foundation.tfplan
```

Review and apply each exact saved artifact before generating the next one.
Terraform plans and `.tfvars` files are ignored locally and must never be
committed.

## Prepare before activating production

Keep RDS stopped and ECS at zero while performing work that does not need the
live application:

1. Run `./scripts/quality.sh` and `./scripts/terraform_quality.sh`.
2. Merge the reviewed change to `master`.
3. Record the candidate's full commit SHA.
4. Dispatch `Deploy production` for that SHA.
5. Let image publication and the read-only Terraform plan finish.
6. Leave the workflow waiting at the protected `production` approval gate.

From a terminal:

```sh
export PORTFOLIO_RAG_CANDIDATE_SHA="$(git rev-parse origin/master)"

gh workflow run deploy-production.yml \
  --repo babaksoft/portfolio-rag-lab \
  --ref master \
  -f "revision=$PORTFOLIO_RAG_CANDIDATE_SHA"

gh run list \
  --repo babaksoft/portfolio-rag-lab \
  --workflow deploy-production.yml \
  --event workflow_dispatch \
  --limit 3
```

Do not approve the protected apply job until RDS is available and the live
test window is ready to begin.

## Activate at the start of the test window

Start the retained database and wait for recovery:

```sh
aws rds start-db-instance \
  --region "$AWS_REGION" \
  --db-instance-identifier "$PORTFOLIO_RAG_DATABASE"

aws rds wait db-instance-available \
  --region "$AWS_REGION" \
  --db-instance-identifier "$PORTFOLIO_RAG_DATABASE"
```

If RDS reports that it is already available, verify its status instead of
repeating the start call:

```sh
aws rds describe-db-instances \
  --region "$AWS_REGION" \
  --db-instance-identifier "$PORTFOLIO_RAG_DATABASE" \
  --query 'DBInstances[0].DBInstanceStatus' \
  --output text
```

Approve the waiting `production` job in GitHub, then watch the run:

```sh
gh run watch RUN_ID \
  --repo babaksoft/portfolio-rag-lab \
  --interval 10 \
  --exit-status
```

The workflow runs the migration, applies the exact saved image-deployment
plan, waits for ECS stability, and compares the running image digests with ECR.
Its deployment helper restores the prior ECS task definition if apply or digest
verification fails.

## Smoke test while production is live

Run the non-interactive checks first:

```sh
aws ecs describe-services \
  --region "$AWS_REGION" \
  --cluster "$PORTFOLIO_RAG_CLUSTER" \
  --services "$PORTFOLIO_RAG_SERVICE" \
  --query 'services[0].{desired:desiredCount,running:runningCount,pending:pendingCount,taskDefinition:taskDefinition,rollout:deployments[0].rolloutState}'

curl --fail --silent --show-error \
  https://portfolio-rag.babaksoft.dev/signed-out >/dev/null

curl --silent --show-error --dump-header - --output /dev/null \
  https://portfolio-rag.babaksoft.dev/auth/logout

aws logs tail /ecs/portfolio-rag-production/api \
  --region "$AWS_REGION" --since 10m
aws logs tail /ecs/portfolio-rag-production/ui \
  --region "$AWS_REGION" --since 10m
```

Then use a clean browser session:

1. Open `https://portfolio-rag.babaksoft.dev`.
2. Complete Google sign-in with a Cognito `reviewers` user.
3. Submit one message and confirm the explicit placeholder response.
4. Sign out and confirm `/signed-out` loads in the same tab.
5. Select **Sign in again** and submit a second message.
6. Confirm the second placeholder response appears without a 401 or 403.

Refreshing an old `/oauth2/idpresponse` callback URL can produce a one-time 401
because the OAuth code and state are no longer reusable. Navigate to the root
URL to begin a fresh flow. A 401 from a fresh root flow is a defect and must be
investigated before promotion.

After all checks pass, record the candidate SHA as the new stable SHA. If this
was intentionally experimental, roll back before suspending.

## Preferred rollback: deploy the stable commit

The preferred rollback uses the same protected workflow and immutable images:

```sh
git fetch origin
git merge-base --is-ancestor "$PORTFOLIO_RAG_STABLE_SHA" origin/master

gh workflow run deploy-production.yml \
  --repo babaksoft/portfolio-rag-lab \
  --ref master \
  -f "revision=$PORTFOLIO_RAG_STABLE_SHA"

gh run list \
  --repo babaksoft/portfolio-rag-lab \
  --workflow deploy-production.yml \
  --event workflow_dispatch \
  --limit 3
```

Review its plan, approve the protected job, watch it to completion, and repeat
the full smoke test. Do not use this path if the candidate ran a migration that
is incompatible with the stable application revision.

## Emergency rollback: restore a prior task definition

Before every experiment, record the currently healthy task definition:

```sh
aws ecs describe-services \
  --region "$AWS_REGION" \
  --cluster "$PORTFOLIO_RAG_CLUSTER" \
  --services "$PORTFOLIO_RAG_SERVICE" \
  --query 'services[0].taskDefinition' \
  --output text > /tmp/portfolio-rag-last-good-task-definition
```

If the protected workflow cannot run and the new service is broken, restore
that exact revision:

```sh
export PORTFOLIO_RAG_LAST_GOOD_TASK_DEFINITION="$(tr -d '\n' < /tmp/portfolio-rag-last-good-task-definition)"

aws ecs update-service \
  --region "$AWS_REGION" \
  --cluster "$PORTFOLIO_RAG_CLUSTER" \
  --service "$PORTFOLIO_RAG_SERVICE" \
  --desired-count 1 \
  --task-definition "$PORTFOLIO_RAG_LAST_GOOD_TASK_DEFINITION"

aws ecs wait services-stable \
  --region "$AWS_REGION" \
  --cluster "$PORTFOLIO_RAG_CLUSTER" \
  --services "$PORTFOLIO_RAG_SERVICE"

./scripts/aws_verify_deployment.sh "$PORTFOLIO_RAG_STABLE_TAG"
```

This emergency action creates Terraform drift. Follow it with a protected
deployment of `PORTFOLIO_RAG_STABLE_SHA`; never edit Terraform state by hand.

## Suspend production after testing

The locally generated saved plan is:

```text
terraform/production/manual-suspend.tfplan
```

It was generated on 2026-11-24 for application image tag
`sha-dfa93e0128102bf181ac48a53df8ecd34867d954` and was verified to contain only:

```text
aws_ecs_service.application desired_count: 1 -> 0
```

Saved plans are state-specific. Before applying it, confirm that no deployment
or Terraform apply has occurred since generation:

```sh
terraform -chdir=terraform/production show manual-suspend.tfplan

terraform -chdir=terraform/production show -json manual-suspend.tfplan |
  jq '[.resource_changes[]
    | select(.change.actions != ["no-op"] and .change.actions != ["read"])
    | {address, actions: .change.actions,
       before_desired_count: .change.before.desired_count,
       after_desired_count: .change.after.desired_count}]'
```

Apply it only if the output still shows the single desired-count update:

```sh
terraform -chdir=terraform/production apply \
  -input=false manual-suspend.tfplan

aws ecs wait services-stable \
  --region "$AWS_REGION" \
  --cluster "$PORTFOLIO_RAG_CLUSTER" \
  --services "$PORTFOLIO_RAG_SERVICE"

aws ecs describe-services \
  --region "$AWS_REGION" \
  --cluster "$PORTFOLIO_RAG_CLUSTER" \
  --services "$PORTFOLIO_RAG_SERVICE" \
  --query 'services[0].{desired:desiredCount,running:runningCount,pending:pendingCount}'
```

Expected counts are all zero. Only then stop RDS:

```sh
aws rds stop-db-instance \
  --region "$AWS_REGION" \
  --db-instance-identifier "$PORTFOLIO_RAG_DATABASE"

aws rds wait db-instance-stopped \
  --region "$AWS_REGION" \
  --db-instance-identifier "$PORTFOLIO_RAG_DATABASE"

aws rds describe-db-instances \
  --region "$AWS_REGION" \
  --db-instance-identifier "$PORTFOLIO_RAG_DATABASE" \
  --query 'DBInstances[0].DBInstanceStatus' \
  --output text
```

If the saved plan is stale, regenerate it instead of forcing it:

```sh
terraform -chdir=terraform/production plan \
  -input=false -lock=false \
  -var-file=terraform.tfvars \
  -var="api_image_tag=$PORTFOLIO_RAG_STABLE_TAG" \
  -var="ui_image_tag=$PORTFOLIO_RAG_STABLE_TAG" \
  -var=service_desired_count=0 \
  -out=manual-suspend.tfplan
```

Review the regenerated plan exactly as above before applying it.

## Resume without deploying a new revision

Start RDS and wait for it to become available. Then create a fresh resume plan:

```sh
aws rds start-db-instance \
  --region "$AWS_REGION" \
  --db-instance-identifier "$PORTFOLIO_RAG_DATABASE"
aws rds wait db-instance-available \
  --region "$AWS_REGION" \
  --db-instance-identifier "$PORTFOLIO_RAG_DATABASE"

terraform -chdir=terraform/production plan \
  -input=false -lock=false \
  -var-file=terraform.tfvars \
  -var="api_image_tag=$PORTFOLIO_RAG_STABLE_TAG" \
  -var="ui_image_tag=$PORTFOLIO_RAG_STABLE_TAG" \
  -var=service_desired_count=1 \
  -out=manual-resume.tfplan

terraform -chdir=terraform/production show manual-resume.tfplan
```

Apply only if it contains the single ECS desired-count change from zero to one:

```sh
terraform -chdir=terraform/production apply \
  -input=false manual-resume.tfplan

aws ecs wait services-stable \
  --region "$AWS_REGION" \
  --cluster "$PORTFOLIO_RAG_CLUSTER" \
  --services "$PORTFOLIO_RAG_SERVICE"
```

Repeat the complete smoke test after resuming.

## Long idle periods and full teardown

For an idle period longer than a short test window, prefer a complete reviewed
teardown. Confirm the final snapshot identifier in the plan is unique, retain
required image digests and operational evidence, and generate the artifact:

```sh
terraform -chdir=terraform/production plan \
  -destroy \
  -input=false \
  -var-file=terraform.tfvars \
  -out=full-teardown.tfplan

terraform -chdir=terraform/production show full-teardown.tfplan
```

Apply only the exact reviewed plan manually. Confirm afterward that the remote
production state has no managed resources and that the expected RDS final
snapshot is available. Do not destroy the separate bootstrap root, state
bucket, IAM permission boundaries, retained ECR images or snapshots, registered
domain, or external Google OAuth client as part of this procedure.

Do not attempt a partial cold teardown with commands such as:

```text
terraform destroy -target=...
terraform state rm ...
aws elbv2 delete-load-balancer ...
aws ec2 delete-nat-gateway ...
```

Those operations create unmanaged drift, can leave broken Route 53 and ECS
references, and make recovery dependent on operator memory. Use the complete
destroy plan even when only the ALB or NAT gateway is driving the cost decision.
