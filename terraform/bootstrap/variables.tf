variable "aws_region" {
  description = "AWS region in which the Terraform state bucket is created. Defaults to the selected production home region."
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment recorded in tags on bootstrap resources."
  type        = string
  default     = "production"
}

variable "state_bucket_name" {
  description = "Globally unique S3 bucket name used for encrypted Terraform state and native lockfiles."
  type        = string
  default     = "portfolio-rag-lab-tfstate-509399640122-us-east-1"

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$", var.state_bucket_name))
    error_message = "state_bucket_name must be a valid, globally unique S3 bucket name."
  }
}

variable "state_key_prefix" {
  description = "S3 object-key prefix reserved for the production Terraform state and lockfile."
  type        = string
  default     = "portfolio-rag-lab/production"

  validation {
    condition     = can(regex("^[A-Za-z0-9][A-Za-z0-9._/-]*[A-Za-z0-9]$", var.state_key_prefix))
    error_message = "state_key_prefix must be a non-empty S3 key prefix without leading or trailing slashes."
  }
}

variable "hosted_zone_id" {
  description = "Route 53 public hosted zone ID to which the Terraform operator's DNS writes are restricted."
  type        = string
  default     = "Z06495321W44G2MBDFW2H"

  validation {
    condition     = can(regex("^Z[A-Z0-9]+$", var.hosted_zone_id))
    error_message = "hosted_zone_id must be a Route 53 hosted zone ID beginning with Z."
  }
}

variable "hosted_zone_name" {
  description = "Registered DNS domain served by hosted_zone_id, without a trailing dot."
  type        = string
  default     = "babaksoft.dev"

  validation {
    condition     = can(regex("^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$", var.hosted_zone_name))
    error_message = "hosted_zone_name must be a valid lower-case DNS domain without a trailing dot."
  }
}

variable "application_hostname" {
  description = "Public application hostname allowed in ACM certificate requests."
  type        = string
  default     = "portfolio-rag.babaksoft.dev"

  validation {
    condition     = can(regex("^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$", var.application_hostname))
    error_message = "application_hostname must be a valid lower-case DNS hostname."
  }
}

variable "github_repository" {
  description = "GitHub owner and repository allowed to exchange Actions OIDC tokens for project roles."
  type        = string
  default     = "babaksoft/portfolio-rag-lab"

  validation {
    condition     = can(regex("^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", var.github_repository))
    error_message = "github_repository must use the owner/repository format."
  }
}
