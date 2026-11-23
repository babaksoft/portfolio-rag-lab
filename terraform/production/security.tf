resource "aws_security_group" "edge" {
  name        = "${local.name_prefix}-edge"
  description = "Future public TLS load balancer boundary"
  vpc_id      = aws_vpc.main.id

  tags = { Name = "${local.name_prefix}-edge" }
}

resource "aws_security_group" "application" {
  name        = "${local.name_prefix}-application"
  description = "Application task boundary"
  vpc_id      = aws_vpc.main.id

  tags = { Name = "${local.name_prefix}-application" }
}

resource "aws_security_group" "database" {
  name        = "${local.name_prefix}-database"
  description = "PostgreSQL access from application tasks only"
  vpc_id      = aws_vpc.main.id

  tags = { Name = "${local.name_prefix}-database" }
}

resource "aws_vpc_security_group_ingress_rule" "edge_https" {
  security_group_id = aws_security_group.edge.id
  description       = "Public HTTPS"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_vpc_security_group_egress_rule" "edge_to_application" {
  security_group_id            = aws_security_group.edge.id
  description                  = "Streamlit traffic to application tasks"
  ip_protocol                  = "tcp"
  from_port                    = 8501
  to_port                      = 8501
  referenced_security_group_id = aws_security_group.application.id
}

resource "aws_vpc_security_group_egress_rule" "edge_to_api_logout" {
  security_group_id            = aws_security_group.edge.id
  description                  = "Logout traffic to the API adapter"
  ip_protocol                  = "tcp"
  from_port                    = 8000
  to_port                      = 8000
  referenced_security_group_id = aws_security_group.application.id
}

resource "aws_vpc_security_group_ingress_rule" "application_from_edge" {
  security_group_id            = aws_security_group.application.id
  description                  = "Streamlit traffic from the future load balancer"
  ip_protocol                  = "tcp"
  from_port                    = 8501
  to_port                      = 8501
  referenced_security_group_id = aws_security_group.edge.id
}

resource "aws_vpc_security_group_ingress_rule" "api_logout_from_edge" {
  security_group_id            = aws_security_group.application.id
  description                  = "Logout traffic from the load balancer"
  ip_protocol                  = "tcp"
  from_port                    = 8000
  to_port                      = 8000
  referenced_security_group_id = aws_security_group.edge.id
}

resource "aws_vpc_security_group_egress_rule" "application_https" {
  security_group_id = aws_security_group.application.id
  description       = "HTTPS access through the NAT gateway"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_vpc_security_group_egress_rule" "application_to_database" {
  security_group_id            = aws_security_group.application.id
  description                  = "PostgreSQL access"
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432
  referenced_security_group_id = aws_security_group.database.id
}

resource "aws_vpc_security_group_ingress_rule" "database_from_application" {
  security_group_id            = aws_security_group.database.id
  description                  = "PostgreSQL from application tasks"
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432
  referenced_security_group_id = aws_security_group.application.id
}
