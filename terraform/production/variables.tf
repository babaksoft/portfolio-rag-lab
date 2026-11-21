variable "aws_region" {
  description = "AWS region for the production foundation. Defaults to the selected production home region."
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment used in names and tags."
  type        = string
  default     = "production"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,15}$", var.environment))
    error_message = "environment must be 2-16 lowercase letters, digits, or hyphens."
  }
}

variable "hosted_zone_name" {
  description = "Registered DNS domain for the imported Terraform-managed public Route 53 zone, without a trailing dot."
  type        = string
  default     = "babaksoft.dev"

  validation {
    condition     = can(regex("^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$", var.hosted_zone_name))
    error_message = "hosted_zone_name must be a valid lower-case DNS domain without a trailing dot."
  }
}

variable "application_hostname" {
  description = "Public application hostname covered by ACM and contained by hosted_zone_name."
  type        = string
  default     = "portfolio-rag.babaksoft.dev"

  validation {
    condition     = can(regex("^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$", var.application_hostname))
    error_message = "application_hostname must be a valid lower-case DNS hostname."
  }
}

variable "vpc_cidr" {
  description = "Private IPv4 CIDR for the production VPC."
  type        = string
  default     = "10.20.0.0/16"

  validation {
    condition     = can(cidrnetmask(var.vpc_cidr))
    error_message = "vpc_cidr must be a valid IPv4 CIDR."
  }
}

variable "database_instance_class" {
  description = "Cost-controlled RDS instance class; change only after reviewing the saved plan."
  type        = string
  default     = "db.t4g.micro"
}

variable "database_deletion_protection" {
  description = "Protect the production database from Terraform deletion; disable only during an approved teardown."
  type        = bool
  default     = true
}

variable "ecs_task_permissions_boundary_arn" {
  description = "Bootstrap-managed boundary that every ECS execution or application task role must retain."
  type        = string
  default     = "arn:aws:iam::509399640122:policy/portfolio-rag/PortfolioRagEcsTaskBoundary"

  validation {
    condition     = can(regex("^arn:aws:iam::[0-9]{12}:policy/portfolio-rag/PortfolioRagEcsTaskBoundary$", var.ecs_task_permissions_boundary_arn))
    error_message = "ecs_task_permissions_boundary_arn must name the bootstrap-managed Portfolio RAG task boundary."
  }
}

variable "api_image_tag" {
  description = "Immutable API image tag already published to the managed ECR repository."
  type        = string

  validation {
    condition     = var.api_image_tag != "latest" && can(regex("^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$", var.api_image_tag))
    error_message = "api_image_tag must be a valid immutable Docker tag other than latest."
  }
}

variable "ui_image_tag" {
  description = "Immutable UI image tag already published to the managed ECR repository."
  type        = string

  validation {
    condition     = var.ui_image_tag != "latest" && can(regex("^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$", var.ui_image_tag))
    error_message = "ui_image_tag must be a valid immutable Docker tag other than latest."
  }
}

variable "service_desired_count" {
  description = "Desired ECS task count; use zero only for the documented first-deployment migration stage."
  type        = number
  default     = 1

  validation {
    condition     = contains([0, 1], var.service_desired_count)
    error_message = "service_desired_count must be zero or one during Phase 0."
  }
}
