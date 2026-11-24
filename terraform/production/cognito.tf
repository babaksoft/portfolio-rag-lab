resource "aws_cognito_user_pool" "application" {
  name                     = local.name_prefix
  deletion_protection      = "INACTIVE"
  auto_verified_attributes = ["email"]
  username_attributes      = ["email"]

  admin_create_user_config {
    allow_admin_create_user_only = true
  }

  user_attribute_update_settings {
    attributes_require_verification_before_update = ["email"]
  }
}

resource "aws_cognito_user_group" "reviewers" {
  name         = "reviewers"
  description  = "People authorized to review the authenticated portfolio application."
  user_pool_id = aws_cognito_user_pool.application.id
  precedence   = 10
}

resource "aws_cognito_user_pool_domain" "application" {
  domain       = "${local.name_prefix}-${data.aws_caller_identity.current.account_id}"
  user_pool_id = aws_cognito_user_pool.application.id
}

resource "terraform_data" "google_identity_provider" {
  triggers_replace = {
    configuration_script = filesha256("${path.module}/../scripts/configure_google_identity_provider.sh")
    google_client_id     = var.google_oauth_client_id
    secret_arn           = aws_secretsmanager_secret.application.arn
    user_pool_id         = aws_cognito_user_pool.application.id
  }

  provisioner "local-exec" {
    command = "${path.module}/../scripts/configure_google_identity_provider.sh"
    environment = {
      AWS_REGION       = var.aws_region
      GOOGLE_CLIENT_ID = var.google_oauth_client_id
      SECRET_ARN       = aws_secretsmanager_secret.application.arn
      USER_POOL_ID     = aws_cognito_user_pool.application.id
    }
  }
}

resource "aws_cognito_user_pool_client" "load_balancer" {
  name         = "${local.name_prefix}-load-balancer"
  user_pool_id = aws_cognito_user_pool.application.id

  generate_secret                      = true
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["openid", "email"]
  callback_urls                        = ["https://${var.application_hostname}/oauth2/idpresponse"]
  logout_urls                          = [local.signed_out_url]
  supported_identity_providers         = ["Google"]

  access_token_validity  = 60
  id_token_validity      = 60
  refresh_token_validity = 1

  token_validity_units {
    access_token  = "minutes"
    id_token      = "minutes"
    refresh_token = "days"
  }

  prevent_user_existence_errors = "ENABLED"

  depends_on = [terraform_data.google_identity_provider]
}
