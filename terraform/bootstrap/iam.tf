data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

locals {
  ecs_task_boundary_arn = "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:policy/portfolio-rag/PortfolioRagEcsTaskBoundary"

  ecs_task_boundary_policy = templatefile("${path.module}/policies/portfolio-rag-ecs-task-boundary.json.tftpl", {
    account_id    = data.aws_caller_identity.current.account_id
    aws_partition = data.aws_partition.current.partition
    aws_region    = var.aws_region
    name_prefix   = "portfolio-rag-${var.environment}"
  })

  terraform_operator_policy = templatefile("${path.module}/policies/portfolio-rag-terraform-operator.json.tftpl", {
    account_id            = data.aws_caller_identity.current.account_id
    application_hostname  = var.application_hostname
    aws_partition         = data.aws_partition.current.partition
    aws_region            = var.aws_region
    ecs_task_boundary_arn = local.ecs_task_boundary_arn
    hosted_zone_id        = var.hosted_zone_id
    hosted_zone_name      = var.hosted_zone_name
    name_prefix           = "portfolio-rag-${var.environment}"
    state_bucket_name     = var.state_bucket_name
    state_key_prefix      = var.state_key_prefix
  })
}

resource "aws_iam_policy" "terraform_operator_boundary" {
  name        = "PortfolioRagTerraformOperatorBoundary"
  path        = "/portfolio-rag/"
  description = "Maximum permissions for the Portfolio RAG Terraform operator."
  policy      = local.terraform_operator_policy

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_iam_policy" "ecs_task_boundary" {
  name        = "PortfolioRagEcsTaskBoundary"
  path        = "/portfolio-rag/"
  description = "Maximum permissions for Portfolio RAG ECS task roles."
  policy      = local.ecs_task_boundary_policy

  lifecycle {
    prevent_destroy = true
  }
}
