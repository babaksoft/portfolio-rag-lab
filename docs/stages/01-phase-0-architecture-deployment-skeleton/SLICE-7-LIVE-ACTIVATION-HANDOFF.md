# Slice 7 live activation handoff

Status recorded on 2026-11-23. Production is provisioned and the ECS service is
healthy, but interactive sign-in is blocked by the load balancer security group.
Do not treat live verification as complete yet.

## Confirmed diagnosis

Browsing `https://portfolio-rag.babaksoft.dev` reaches the authentication flow,
but the browser receives an internal server error after Google authentication.
The failure is at the Application Load Balancer authentication boundary:

- The application URL returns `302` to the Cognito authorization endpoint.
- Cognito returns `302` to Google's authorization endpoint.
- Google federation succeeded far enough to create an external-provider user in
  the Cognito user pool.
- CloudWatch exposes `ELBAuthError` for the production load balancer.
- No corresponding browser request reaches the UI container; the API and UI
  tasks remain healthy.
- The ALB edge security group currently allows outbound traffic only to the ECS
  task security group on ports 8501 and 8000.

After Cognito redirects the authorization grant back to
`/oauth2/idpresponse`, the ALB must call Cognito's token endpoint over HTTPS.
The edge security group blocks that outbound TCP 443 request, causing the 500.
Incognito mode cannot avoid this because it is a server-side networking error.

## Required fix

Add a Terraform-managed egress rule to `terraform/production/security.tf` for
the edge security group:

```hcl
resource "aws_vpc_security_group_egress_rule" "edge_https" {
  security_group_id = aws_security_group.edge.id
  description       = "HTTPS access to Cognito authentication endpoints"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
  cidr_ipv4         = "0.0.0.0/0"
}
```

This is intended only to let the ALB reach the public Cognito token/user-info
endpoints. The existing ECS target rules on ports 8501 and 8000 remain scoped to
the application security group.

Then:

1. Format and validate the Terraform configuration.
2. Run `./scripts/quality.sh` and `git diff --check`.
3. Create a production Terraform plan using the `portfolio-rag` profile.
4. Confirm that the plan contains only the new edge HTTPS egress rule.
5. Apply the reviewed plan with the `portfolio-rag` profile.
6. Retry sign-in in a clean browser session.
7. Confirm `ELBAuthSuccess` increases, `ELBAuthError` stops increasing, and the
   UI request reaches ECS.
8. Add the federated user to the Cognito `reviewers` group if authorization
   denies access after authentication; then verify the authorized UI/API flow.
9. Re-run the Slice 7 live verification and Terraform drift check.

Do not commit, push, or open a PR without explicit user authorization.

## Live resource references

- AWS region: `us-east-1`
- AWS account: `509399640122`
- Operator profile: `portfolio-rag`
- Administrative profile: `support-desk-bootstrap`
- Cognito user pool: `us-east-1_wJLW4f960`
- Cognito app client: `5ca7o7231cv3ge27hmlq3bl7ol`
- Cognito domain prefix: `portfolio-rag-production-509399640122`
- ALB ARN:
  `arn:aws:elasticloadbalancing:us-east-1:509399640122:loadbalancer/app/portfolio-rag-production/1e1c69973f884ede`
- Google OAuth client ID:
  `962756636955-3rceqhak12e95a311v90805o3d1siphm.apps.googleusercontent.com`
- Google redirect URI:
  `https://portfolio-rag-production-509399640122.auth.us-east-1.amazoncognito.com/oauth2/idpresponse`
- Application callback URI:
  `https://portfolio-rag.babaksoft.dev/oauth2/idpresponse`

No Google client secret is recorded in this file or the repository. Its value
remains in the production Secrets Manager secret.

## Existing uncommitted work

At handoff time, the worktree already contains these intentional, uncommitted
changes from live activation troubleshooting:

- `terraform/scripts/configure_google_identity_provider.sh`: use a mode-0600
  memory-backed temporary JSON input for the AWS CLI, then delete it.
- `terraform/README.md`: document that secret-handling behavior.
- `terraform/bootstrap/policies/portfolio-rag-terraform-operator.json.tftpl`:
  grant `logs:FilterLogEvents` while keeping the IAM policy below its size
  limit by compacting ECR read actions.

Preserve those changes. No edge HTTPS rule has been added or applied yet.

## Previously completed activation checks

- Production Terraform had converged before this authentication defect was
  found.
- ECS desired/running count was 1/1 with completed rollout.
- Both containers were healthy and used the expected immutable image digests.
- The ALB UI target was healthy.
- The ECS task had no public IP.
- RDS was private, encrypted, deletion-protected, and available.
- Migration completed successfully.
- ECR scans completed with no critical findings.
- Pre-login application logs contained no relevant errors or secret leakage.
