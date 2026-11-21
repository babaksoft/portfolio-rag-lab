output "state_bucket_name" {
  description = "Bucket name to place in the production backend configuration."
  value       = aws_s3_bucket.terraform_state.id
}

output "state_bucket_region" {
  description = "Bucket region to place in the production backend configuration."
  value       = var.aws_region
}

output "terraform_operator_boundary_arn" {
  description = "Boundary ARN to attach to the IAM Identity Center Terraform operator permission set."
  value       = aws_iam_policy.terraform_operator_boundary.arn
}

output "terraform_operator_boundary_name" {
  description = "Customer-managed boundary name used by the IAM Identity Center permission set."
  value       = aws_iam_policy.terraform_operator_boundary.name
}

output "ecs_task_boundary_arn" {
  description = "Mandatory permissions boundary ARN for ECS execution and task roles."
  value       = aws_iam_policy.ecs_task_boundary.arn
}

output "terraform_operator_policy_json" {
  description = "Rendered inline policy to attach to the IAM Identity Center Terraform operator permission set."
  value       = local.terraform_operator_policy
}

output "github_actions_role_arns" {
  description = "Short-lived OIDC role ARNs used by the GitHub delivery workflow."
  value = {
    deploy  = aws_iam_role.github_deploy.arn
    plan    = aws_iam_role.github_plan.arn
    publish = aws_iam_role.github_publish.arn
  }
}
