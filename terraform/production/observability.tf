resource "aws_sns_topic" "operations" {
  name = "${local.name_prefix}-operations"
}

data "aws_iam_policy_document" "operations_topic" {
  statement {
    sid       = "AccountAdministration"
    effect    = "Allow"
    actions   = ["SNS:*"]
    resources = [aws_sns_topic.operations.arn]

    principals {
      type        = "AWS"
      identifiers = ["arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:root"]
    }
  }

  statement {
    sid       = "OperationalEvents"
    effect    = "Allow"
    actions   = ["SNS:Publish"]
    resources = [aws_sns_topic.operations.arn]

    principals {
      type = "Service"
      identifiers = [
        "cloudwatch.amazonaws.com",
        "events.rds.amazonaws.com",
      ]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_sns_topic_policy" "operations" {
  arn    = aws_sns_topic.operations.arn
  policy = data.aws_iam_policy_document.operations_topic.json
}

resource "aws_sns_topic_subscription" "operations_email" {
  count = var.operations_alarm_email == null ? 0 : 1

  topic_arn = aws_sns_topic.operations.arn
  protocol  = "email"
  endpoint  = coalesce(var.operations_alarm_email, "unused@example.invalid")
}

resource "aws_cloudwatch_metric_alarm" "service_task_missing" {
  alarm_name          = "${local.name_prefix}-service-task-missing"
  alarm_description   = "Owner: repository owner. ECS has no running application task; follow the incident runbook."
  namespace           = "ECS/ContainerInsights"
  metric_name         = "RunningTaskCount"
  statistic           = "Minimum"
  period              = 60
  evaluation_periods  = 2
  datapoints_to_alarm = 2
  threshold           = 1
  comparison_operator = "LessThanThreshold"
  treat_missing_data  = "breaching"
  alarm_actions       = [aws_sns_topic.operations.arn]
  ok_actions          = [aws_sns_topic.operations.arn]

  dimensions = {
    ClusterName = aws_ecs_cluster.main.name
    ServiceName = aws_ecs_service.application.name
  }
}

resource "aws_cloudwatch_metric_alarm" "unhealthy_targets" {
  alarm_name          = "${local.name_prefix}-unhealthy-targets"
  alarm_description   = "Owner: repository owner. ALB reports an unhealthy UI target; inspect ECS events and correlated logs."
  namespace           = "AWS/ApplicationELB"
  metric_name         = "UnHealthyHostCount"
  statistic           = "Maximum"
  period              = 60
  evaluation_periods  = 2
  datapoints_to_alarm = 2
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.operations.arn]
  ok_actions          = [aws_sns_topic.operations.arn]

  dimensions = {
    LoadBalancer = aws_lb.application.arn_suffix
    TargetGroup  = aws_lb_target_group.ui.arn_suffix
  }
}

resource "aws_cloudwatch_metric_alarm" "load_balancer_errors" {
  alarm_name          = "${local.name_prefix}-load-balancer-5xx"
  alarm_description   = "Owner: repository owner. Repeated target 5xx responses require correlated-log review."
  namespace           = "AWS/ApplicationELB"
  metric_name         = "HTTPCode_Target_5XX_Count"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  datapoints_to_alarm = 1
  threshold           = 5
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.operations.arn]
  ok_actions          = [aws_sns_topic.operations.arn]

  dimensions = {
    LoadBalancer = aws_lb.application.arn_suffix
    TargetGroup  = aws_lb_target_group.ui.arn_suffix
  }
}

resource "aws_cloudwatch_metric_alarm" "database_storage_low" {
  alarm_name          = "${local.name_prefix}-database-storage-low"
  alarm_description   = "Owner: repository owner. RDS free storage is below 2 GiB; inspect growth before service is affected."
  namespace           = "AWS/RDS"
  metric_name         = "FreeStorageSpace"
  statistic           = "Minimum"
  period              = 300
  evaluation_periods  = 2
  datapoints_to_alarm = 2
  threshold           = 2147483648
  comparison_operator = "LessThanThreshold"
  treat_missing_data  = "missing"
  alarm_actions       = [aws_sns_topic.operations.arn]
  ok_actions          = [aws_sns_topic.operations.arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.identifier
  }
}

resource "aws_cloudwatch_metric_alarm" "database_cpu_high" {
  alarm_name          = "${local.name_prefix}-database-cpu-high"
  alarm_description   = "Owner: repository owner. Sustained RDS CPU above 90 percent requires query and capacity review."
  namespace           = "AWS/RDS"
  metric_name         = "CPUUtilization"
  statistic           = "Average"
  period              = 300
  evaluation_periods  = 3
  datapoints_to_alarm = 3
  threshold           = 90
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "missing"
  alarm_actions       = [aws_sns_topic.operations.arn]
  ok_actions          = [aws_sns_topic.operations.arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.identifier
  }
}

resource "aws_db_event_subscription" "operations" {
  name      = "${local.name_prefix}-database-events"
  sns_topic = aws_sns_topic.operations.arn

  source_type = "db-instance"
  source_ids  = [aws_db_instance.main.identifier]
  event_categories = [
    "availability",
    "backup",
    "failure",
    "failover",
    "low storage",
    "maintenance",
    "recovery",
    "restoration",
  ]

  tags = { Owner = "repository-owner" }

  depends_on = [aws_sns_topic_policy.operations]
}
