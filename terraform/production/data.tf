resource "aws_db_subnet_group" "main" {
  name       = local.name_prefix
  subnet_ids = values(aws_subnet.database)[*].id

  tags = { Name = local.name_prefix }
}

resource "aws_db_instance" "main" {
  identifier = local.name_prefix

  engine         = "postgres"
  engine_version = "17"
  instance_class = var.database_instance_class

  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = "portfolio_rag"
  username = "portfolio_rag_admin"
  port     = 5432

  manage_master_user_password = true
  publicly_accessible         = false
  multi_az                    = false

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.database.id]

  backup_retention_period    = 7
  backup_window              = "03:00-04:00"
  maintenance_window         = "sun:04:00-sun:05:00"
  auto_minor_version_upgrade = true
  copy_tags_to_snapshot      = true
  deletion_protection        = false
  skip_final_snapshot        = false
  final_snapshot_identifier = (
    "${local.name_prefix}-final-${formatdate("YYYYMMDDhhmmss", plantimestamp())}"
  )

  apply_immediately = false

  lifecycle {
    # Allocate the teardown snapshot name when this database is created. Later
    # plans must not rotate it merely because their plan timestamp changed.
    ignore_changes = [final_snapshot_identifier]
  }
}

resource "aws_secretsmanager_secret" "application" {
  name = (
    "${local.name_prefix}/application-${formatdate("YYYYMMDDhhmmss", plantimestamp())}"
  )
  description             = "Runtime application secrets populated outside Terraform."
  recovery_window_in_days = 7

  lifecycle {
    # A deleted secret keeps its name during the recovery window. Allocate a
    # fresh name on reconstruction, then keep it stable for this environment.
    ignore_changes = [name]
  }
}
