locals {
  github_oidc_url = "https://token.actions.githubusercontent.com"

  github_plan_policy = templatefile("${path.module}/policies/portfolio-rag-github-plan.json.tftpl", {
    aws_partition     = data.aws_partition.current.partition
    state_bucket_name = var.state_bucket_name
    state_key_prefix  = var.state_key_prefix
  })

  github_publish_policy = templatefile("${path.module}/policies/portfolio-rag-github-publish.json.tftpl", {
    account_id    = data.aws_caller_identity.current.account_id
    aws_partition = data.aws_partition.current.partition
    aws_region    = var.aws_region
  })

  github_deploy_policy = templatefile("${path.module}/policies/portfolio-rag-github-deploy.json.tftpl", {
    account_id        = data.aws_caller_identity.current.account_id
    aws_partition     = data.aws_partition.current.partition
    aws_region        = var.aws_region
    name_prefix       = "portfolio-rag-${var.environment}"
    state_bucket_name = var.state_bucket_name
    state_key_prefix  = var.state_key_prefix
  })
}

data "aws_iam_openid_connect_provider" "github_actions" {
  url = local.github_oidc_url
}

data "aws_iam_policy_document" "github_master_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [data.aws_iam_openid_connect_provider.github_actions.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_repository}:ref:refs/heads/master"]
    }
  }
}

resource "aws_iam_role" "github_plan" {
  name                 = "portfolio-rag-github-plan"
  description          = "Read-only production planning role for the master delivery workflow."
  assume_role_policy   = data.aws_iam_policy_document.github_master_assume_role.json
  max_session_duration = 3600
}

resource "aws_iam_role_policy" "github_plan" {
  name   = "production-plan"
  role   = aws_iam_role.github_plan.id
  policy = local.github_plan_policy
}

resource "aws_iam_role" "github_publish" {
  name                 = "portfolio-rag-github-publish"
  description          = "Immutable ECR image publisher for revisions on master."
  assume_role_policy   = data.aws_iam_policy_document.github_master_assume_role.json
  max_session_duration = 3600
}

resource "aws_iam_role_policy" "github_publish" {
  name   = "publish-application-images"
  role   = aws_iam_role.github_publish.id
  policy = local.github_publish_policy
}

data "aws_iam_policy_document" "github_deploy_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [data.aws_iam_openid_connect_provider.github_actions.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_repository}:environment:production"]
    }
  }
}

resource "aws_iam_role" "github_deploy" {
  name                 = "portfolio-rag-github-deploy"
  description          = "Protected-environment role for approved production deployments."
  assume_role_policy   = data.aws_iam_policy_document.github_deploy_assume_role.json
  permissions_boundary = aws_iam_policy.terraform_operator_boundary.arn
  max_session_duration = 3600
}

resource "aws_iam_role_policy" "github_deploy" {
  name   = "approved-production-deploy"
  role   = aws_iam_role.github_deploy.id
  policy = local.github_deploy_policy
}
