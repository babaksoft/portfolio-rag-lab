# Operational readiness runbook

This runbook owns Phase 0 diagnosis, failure drills, recovery evidence, and the
final live smoke checklist. The repository owner is the operational and alarm
owner. The longer [production lifecycle runbook](production-lifecycle-runbook.md)
owns reconstruction, deployment, rollback, suspension, and teardown commands.

## Availability and health contract

- `/health/live` reports only whether the API process can serve requests. It
  never probes the network or database.
- `/health/ready` performs a bounded database probe. It returns `503` with no
  infrastructure detail when PostgreSQL is unavailable.
- The ECS API health check uses readiness. Repeated database failure therefore
  removes the single application task and ECS attempts replacement. This is a
  visible outage, not high availability.
- The ALB probes Streamlit and the unauthenticated API logout target. A healthy
  edge target proves process reachability, not that an authenticated message
  exchange or database transaction succeeds.
- Deployment circuit breaking restores the previous task definition when a new
  task cannot stabilize. Database migrations are separate and are not reversed
  automatically.

## Logs, correlation, and safe diagnosis

The API and UI emit one-line JSON logs to their existing CloudWatch log groups.
Application records contain a stable event, service, severity, correlation ID
where applicable, outcome, latency, status, and bounded error category. They do
not contain messages, identity attributes, tokens, assertions, passwords,
exception text, or request and response bodies. Log groups retain data for
`log_retention_days`, 30 days by default.

For a correlation ID shown by the UI, query both processes:

```sh
export PORTFOLIO_RAG_CORRELATION_ID=REPLACE_WITH_SAFE_ID

aws logs filter-log-events \
  --region "$AWS_REGION" \
  --log-group-name /ecs/portfolio-rag-production/ui \
  --filter-pattern "{$.correlation_id = \"$PORTFOLIO_RAG_CORRELATION_ID\"}"

aws logs filter-log-events \
  --region "$AWS_REGION" \
  --log-group-name /ecs/portfolio-rag-production/api \
  --filter-pattern "{$.correlation_id = \"$PORTFOLIO_RAG_CORRELATION_ID\"}"
```

The expected authenticated path is `backend_request_completed` in UI logs,
then API authentication and identity events and `request_completed` with the
same identifier. Database identity resolution is represented by the bounded
`identity_resolved` event; SQL and identity attributes are intentionally absent.

## Alarms and first response

Terraform creates an SNS operations topic and alarms for a missing ECS task,
unhealthy ALB target, repeated target 5xx responses, sustained high RDS CPU,
and low RDS free storage. RDS availability, backup, failure, low-storage,
maintenance, recovery, and restoration events use the same topic. Set
`operations_alarm_email`, apply it, and confirm the SNS email subscription;
an unconfirmed subscription does not deliver notifications.

Before the first production plan, apply the reviewed bootstrap operator-boundary
and GitHub plan-role read-permission changes, then reprovision the matching IAM
Identity Center permission set. The production alarm apply otherwise fails
closed at its new CloudWatch, SNS, and RDS event-subscription permissions.

On an alarm:

1. Confirm account `509399640122`, region `us-east-1`, current operating state,
   and alarm transition time. A deliberately suspended or cold environment is
   not an incident.
2. Inspect ECS service events, stopped-task reasons, target health, RDS status,
   and the alarm's source metric. Do not paste tokens or secret values into an
   incident record.
3. Use a correlation ID to inspect bounded UI and API events. Classify the
   incident as task, edge, database, configuration, authentication, or deploy.
4. Recover with the lifecycle runbook. Preserve the previous healthy task
   definition and never downgrade a migration automatically.
5. Record timeline, impact, recovery action, and follow-up in the Phase 0
   implementation record. Resolve the alarm only after smoke checks pass.

## Required live failure drills

Run these only in an approved active test window. Capture commands, timestamps,
alarm delivery, bounded log events, recovery duration, and final smoke result.
Never inject a real secret as a failure value.

- **Task failure:** stop the sole service task. Confirm a missing or unhealthy
  signal, the expected outage, automatic replacement, a new task ID, and
  healthy targets afterward.
- **Database unavailable:** stop RDS. Confirm readiness `503`, liveness `200`
  from a suitable in-VPC probe, safe client behavior, an RDS event or alarm,
  and recovery after RDS and ECS stabilize.
- **Bad configuration:** deploy a reviewed task definition with a harmless
  invalid required setting, such as an invalid authentication mode. Confirm
  startup failure contains no environment values and circuit rollback restores
  the last healthy revision.
- **Failed deployment:** deploy a non-starting candidate through the approved
  path. Confirm the workflow and ECS circuit breaker preserve or restore the
  prior task definition and that migrations were not reversed.

## Backups, migrations, and secrets

The RDS instance retains seven days of automated backups, uses a fixed backup
window, creates a final snapshot on deletion, and encrypts storage and the
RDS-managed master credential. During final verification, inspect the latest
restorable time and retained snapshots. Prove restoration into an isolated,
non-public instance before claiming tested database recovery; do not replace
the managed production instance ad hoc.

Apply migrations with `scripts/aws_run_migration.sh` before deployment. A
nonzero migration task blocks activation. Schema changes must remain compatible
with the running and rollback application versions.

RDS owns master-credential rotation. After rotation, replace the ECS task so it
receives the current injected values and run the authenticated smoke test. For
Google OAuth, update only the application Secrets Manager value, run the
documented Terraform reconciliation, verify that plan, state, and logs do not
contain the secret, then test sign-in and sign-out. Never place a secret in a
Terraform variable, command argument, shell history, or incident record.

## Cost visibility

Before each active window, review the Terraform plan and current AWS Cost
Explorer month-to-date charges. Record the estimate date and assumptions for
NAT, public IPv4, ALB, RDS instance and storage, Secrets Manager, Route 53,
CloudWatch logs and alarms, ECR, and traffic. The historical estimate in the
Phase 0 implementation record predates later resources and is not a current
quote. Use suspended or cold state promptly when the verification window ends.

## Final Phase 0 smoke checklist

- Local quality, Terraform quality, shell syntax, and `git diff --check` pass.
- The alarm email subscription is confirmed and every alarm is `OK` after an
  intentional test transition or documented evidence-based review.
- Log retention is bounded; one authenticated exchange is traceable across UI,
  API, identity, and database boundaries without raw content or credentials.
- Liveness and readiness behavior and all four failure drills match this runbook.
- Automated-backup configuration, latest restorable time, final-snapshot
  policy, and an isolated restore are verified.
- Migration failure blocks deploy; failed deploy restores the prior healthy
  application; manual rollback is rechecked.
- Google sign-in, continuation, protected placeholder response, sign-out,
  sign-in again, and stable internal identity all pass.
- Credential rotation paths and leakage inspection pass.
- Current cost evidence and the operating-state decision are recorded.
- Known risks below remain accepted or receive owners before deterministic RAG
  work starts.

## Known Phase 0 risks

- One task, one NAT gateway, and single-AZ RDS create expected outage domains.
- Database unavailability can trigger repeated task replacement until recovery.
- Alarm delivery depends on a confirmed optional email subscription and a human
  repository owner; there is no staffed on-call rotation.
- Cold reconstruction is lengthy and recreates Cognito users and DNS delegation.
- Automated backups are regional; no cross-region disaster recovery exists.
- Google application sign-out does not terminate the upstream Google session or
  already-open Streamlit tabs.
- Image findings below the critical deployment gate remain maintenance work.
- CloudWatch and Cost Explorer provide visibility, not a project-scoped hard
  spending cap.
