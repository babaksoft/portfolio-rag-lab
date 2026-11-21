locals {
  name_prefix = "portfolio-rag-${var.environment}"

  common_tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
    Project     = "portfolio-rag-lab"
  }

  availability_zones = slice(data.aws_availability_zones.available.names, 0, 2)
  public_subnet_cidrs = {
    for index, zone in local.availability_zones : zone => cidrsubnet(var.vpc_cidr, 8, index)
  }
  application_subnet_cidrs = {
    for index, zone in local.availability_zones : zone => cidrsubnet(var.vpc_cidr, 8, index + 16)
  }
  database_subnet_cidrs = {
    for index, zone in local.availability_zones : zone => cidrsubnet(var.vpc_cidr, 8, index + 32)
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}
