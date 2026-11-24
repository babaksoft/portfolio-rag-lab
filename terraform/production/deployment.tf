resource "aws_lb" "application" {
  name               = local.name_prefix
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.edge.id]
  subnets            = values(aws_subnet.public)[*].id

  drop_invalid_header_fields = true
  enable_deletion_protection = true

  tags = { Name = local.name_prefix }
}

resource "aws_lb_target_group" "ui" {
  name        = "${local.name_prefix}-ui"
  port        = 8501
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = aws_vpc.main.id

  deregistration_delay = 30

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 15
    matcher             = "200"
    path                = "/_stcore/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 3
  }
}

resource "aws_lb_target_group" "api_logout" {
  name        = "${local.name_prefix}-logout"
  port        = 8000
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = aws_vpc.main.id

  deregistration_delay = 30

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 15
    matcher             = "200"
    path                = "/health/live"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 3
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.application.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = aws_acm_certificate_validation.application.certificate_arn

  default_action {
    order = 1
    type  = "authenticate-cognito"

    authenticate_cognito {
      user_pool_arn       = aws_cognito_user_pool.application.arn
      user_pool_client_id = aws_cognito_user_pool_client.load_balancer.id
      user_pool_domain    = aws_cognito_user_pool_domain.application.domain
      scope               = "openid email"
      session_cookie_name = "AWSELBAuthSessionCookie"
      session_timeout     = 3600
    }
  }

  default_action {
    order            = 2
    type             = "forward"
    target_group_arn = aws_lb_target_group.ui.arn
  }
}

resource "aws_lb_listener_rule" "logout" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 1

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api_logout.arn
  }

  condition {
    path_pattern {
      values = ["/auth/logout"]
    }
  }
}

resource "aws_lb_listener_rule" "signed_out" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 2

  action {
    type = "fixed-response"

    fixed_response {
      content_type = "text/html"
      message_body = <<-HTML
        <!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Signed out</title></head><body><main><h1>Signed out</h1><p>Your application session has ended. Your Google session may still be active, so you may be signed in automatically if you return.</p><p><a href="/">Sign in again</a></p></main></body></html>
      HTML
      status_code  = "200"
    }
  }

  condition {
    path_pattern {
      values = ["/signed-out"]
    }
  }
}

resource "aws_route53_record" "application" {
  zone_id = aws_route53_zone.main.zone_id
  name    = var.application_hostname
  type    = "A"

  alias {
    name                   = aws_lb.application.dns_name
    zone_id                = aws_lb.application.zone_id
    evaluate_target_health = true
  }
}

locals {
  database_environment = [
    {
      name  = "PORTFOLIO_RAG_API_DATABASE_HOST"
      value = aws_db_instance.main.address
    },
    {
      name  = "PORTFOLIO_RAG_API_DATABASE_PORT"
      value = tostring(aws_db_instance.main.port)
    },
    {
      name  = "PORTFOLIO_RAG_API_DATABASE_NAME"
      value = aws_db_instance.main.db_name
    },
  ]
  database_secrets = [
    {
      name      = "PORTFOLIO_RAG_API_DATABASE_USERNAME"
      valueFrom = "${one(aws_db_instance.main.master_user_secret).secret_arn}:username::"
    },
    {
      name      = "PORTFOLIO_RAG_API_DATABASE_PASSWORD"
      valueFrom = "${one(aws_db_instance.main.master_user_secret).secret_arn}:password::"
    },
  ]
  api_image = "${aws_ecr_repository.api.repository_url}:${var.api_image_tag}"
  ui_image  = "${aws_ecr_repository.ui.repository_url}:${var.ui_image_tag}"
  log_configuration = {
    logDriver = "awslogs"
    options = {
      awslogs-region        = var.aws_region
      awslogs-stream-prefix = "ecs"
    }
  }
}

resource "aws_ecs_task_definition" "application" {
  family                   = local.name_prefix
  skip_destroy             = true
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.application_task.arn

  runtime_platform {
    cpu_architecture        = "X86_64"
    operating_system_family = "LINUX"
  }

  container_definitions = jsonencode([
    {
      name      = "api"
      image     = local.api_image
      essential = true
      cpu       = 256
      memory    = 512
      environment = concat(local.database_environment, [
        {
          name  = "PORTFOLIO_RAG_API_DATABASE_CONNECTION_TIMEOUT_SECONDS"
          value = "2"
        },
        {
          name  = "PORTFOLIO_RAG_API_AUTHENTICATION_MODE"
          value = "alb_cognito"
        },
        {
          name  = "PORTFOLIO_RAG_API_AWS_REGION"
          value = var.aws_region
        },
        {
          name  = "PORTFOLIO_RAG_API_ALB_ARN"
          value = aws_lb.application.arn
        },
        {
          name  = "PORTFOLIO_RAG_API_COGNITO_USER_POOL_ID"
          value = aws_cognito_user_pool.application.id
        },
        {
          name  = "PORTFOLIO_RAG_API_COGNITO_CLIENT_ID"
          value = aws_cognito_user_pool_client.load_balancer.id
        },
        {
          name  = "PORTFOLIO_RAG_API_COGNITO_DOMAIN"
          value = "${aws_cognito_user_pool_domain.application.domain}.auth.${var.aws_region}.amazoncognito.com"
        },
        {
          name  = "PORTFOLIO_RAG_API_APPLICATION_URL"
          value = local.signed_out_url
        },
        {
          name  = "PORTFOLIO_RAG_API_AUTHORIZED_GROUP"
          value = aws_cognito_user_group.reviewers.name
        },
      ])
      secrets = local.database_secrets
      portMappings = [{
        containerPort = 8000
        hostPort      = 8000
        protocol      = "tcp"
      }]
      healthCheck = {
        command = [
          "CMD-SHELL",
          "python -c \"from urllib.request import urlopen; urlopen('http://127.0.0.1:8000/health/ready', timeout=1).read()\"",
        ]
        interval    = 10
        retries     = 3
        startPeriod = 30
        timeout     = 3
      }
      logConfiguration = merge(local.log_configuration, {
        options = merge(local.log_configuration.options, {
          awslogs-group = aws_cloudwatch_log_group.api.name
        })
      })
    },
    {
      name      = "ui"
      image     = local.ui_image
      essential = true
      cpu       = 256
      memory    = 512
      portMappings = [{
        containerPort = 8501
        hostPort      = 8501
        protocol      = "tcp"
      }]
      environment = [
        {
          name  = "PORTFOLIO_RAG_UI_API_BASE_URL"
          value = "http://127.0.0.1:8000"
        },
        {
          name  = "PORTFOLIO_RAG_UI_API_TIMEOUT_SECONDS"
          value = "5"
        },
      ]
      dependsOn = [{
        containerName = "api"
        condition     = "HEALTHY"
      }]
      healthCheck = {
        command = [
          "CMD-SHELL",
          "python -c \"from urllib.request import urlopen; urlopen('http://127.0.0.1:8501/_stcore/health', timeout=1).read()\"",
        ]
        interval    = 10
        retries     = 3
        startPeriod = 30
        timeout     = 3
      }
      logConfiguration = merge(local.log_configuration, {
        options = merge(local.log_configuration.options, {
          awslogs-group = aws_cloudwatch_log_group.ui.name
        })
      })
    },
  ])
}

resource "aws_ecs_task_definition" "migration" {
  family                   = "${local.name_prefix}-migration"
  skip_destroy             = true
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.application_task.arn

  runtime_platform {
    cpu_architecture        = "X86_64"
    operating_system_family = "LINUX"
  }

  container_definitions = jsonencode([{
    name        = "migration"
    image       = local.api_image
    essential   = true
    command     = ["alembic", "upgrade", "head"]
    environment = local.database_environment
    secrets     = local.database_secrets
    stopTimeout = 30
    logConfiguration = merge(local.log_configuration, {
      options = merge(local.log_configuration.options, {
        awslogs-group = aws_cloudwatch_log_group.api.name
      })
    })
  }])
}

resource "aws_ecs_service" "application" {
  name             = local.name_prefix
  cluster          = aws_ecs_cluster.main.id
  task_definition  = aws_ecs_task_definition.application.arn
  desired_count    = var.service_desired_count
  launch_type      = "FARGATE"
  platform_version = "LATEST"

  deployment_minimum_healthy_percent = 0
  deployment_maximum_percent         = 100
  health_check_grace_period_seconds  = 60
  wait_for_steady_state              = true

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  network_configuration {
    assign_public_ip = false
    security_groups  = [aws_security_group.application.id]
    subnets          = values(aws_subnet.application)[*].id
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.ui.arn
    container_name   = "ui"
    container_port   = 8501
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api_logout.arn
    container_name   = "api"
    container_port   = 8000
  }

  depends_on = [aws_lb_listener_rule.logout]
}
