output "aws_account_id" {
  description = "AWS account in which the foundation is managed."
  value       = data.aws_caller_identity.current.account_id
}

output "aws_region" {
  description = "AWS home region selected for the foundation."
  value       = var.aws_region
}

output "application_hostname" {
  description = "Public hostname reserved for the application."
  value       = var.application_hostname
}

output "route53_name_servers" {
  description = "Authoritative name servers of the imported Route 53 public zone."
  value       = aws_route53_zone.main.name_servers
}

output "certificate_arn" {
  description = "ACM certificate ARN for the future HTTPS listener."
  value       = aws_acm_certificate_validation.application.certificate_arn
}

output "ecs_cluster_arn" {
  description = "ECS cluster ARN for the future application service."
  value       = aws_ecs_cluster.main.arn
}

output "application_subnet_ids" {
  description = "Private subnet IDs for future ECS tasks."
  value       = values(aws_subnet.application)[*].id
}

output "application_subnet_ids_csv" {
  description = "Private application subnet IDs formatted for the manual ECS migration command."
  value       = join(",", values(aws_subnet.application)[*].id)
}

output "public_subnet_ids" {
  description = "Public subnet IDs for the future application load balancer."
  value       = values(aws_subnet.public)[*].id
}

output "application_security_group_id" {
  description = "Security group ID for future application tasks."
  value       = aws_security_group.application.id
}

output "edge_security_group_id" {
  description = "Security group ID for the future application load balancer."
  value       = aws_security_group.edge.id
}

output "database_address" {
  description = "Private RDS endpoint; the managed password remains in Secrets Manager."
  value       = aws_db_instance.main.address
}

output "database_master_secret_arn" {
  description = "ARN of the RDS-managed master credential secret."
  value       = one(aws_db_instance.main.master_user_secret).secret_arn
}

output "application_secret_arn" {
  description = "ARN of the empty application runtime secret container."
  value       = aws_secretsmanager_secret.application.arn
}

output "ecr_repository_urls" {
  description = "Repository URLs used by the later image publishing slice."
  value = {
    api = aws_ecr_repository.api.repository_url
    ui  = aws_ecr_repository.ui.repository_url
  }
}

output "application_url" {
  description = "Public TLS entry point for the deployed Streamlit UI."
  value       = "https://${var.application_hostname}"
}

output "application_task_definition_arn" {
  description = "Task definition used by the one-task application service."
  value       = aws_ecs_task_definition.application.arn
}

output "migration_task_definition_arn" {
  description = "One-off task definition used to apply database migrations before deployment."
  value       = aws_ecs_task_definition.migration.arn
}

output "ecs_service_name" {
  description = "ECS service restored to desired count one after task failure."
  value       = aws_ecs_service.application.name
}
