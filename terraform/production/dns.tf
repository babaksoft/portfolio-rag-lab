resource "aws_route53_zone" "main" {
  name    = var.hosted_zone_name
  comment = "HostedZone created by Route53 Registrar"
}

resource "aws_acm_certificate" "application" {
  domain_name       = var.application_hostname
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true

    precondition {
      condition = (
        var.application_hostname == var.hosted_zone_name ||
        endswith(var.application_hostname, ".${var.hosted_zone_name}")
      )
      error_message = "application_hostname must equal or be a subdomain of hosted_zone_name."
    }
  }
}

resource "aws_route53_record" "certificate_validation" {
  for_each = toset([var.application_hostname])

  allow_overwrite = true
  zone_id         = aws_route53_zone.main.zone_id
  name = one([
    for option in aws_acm_certificate.application.domain_validation_options :
    option.resource_record_name if option.domain_name == each.key
  ])
  records = [one([
    for option in aws_acm_certificate.application.domain_validation_options :
    option.resource_record_value if option.domain_name == each.key
  ])]
  ttl = 60
  type = one([
    for option in aws_acm_certificate.application.domain_validation_options :
    option.resource_record_type if option.domain_name == each.key
  ])
}

resource "aws_acm_certificate_validation" "application" {
  certificate_arn         = aws_acm_certificate.application.arn
  validation_record_fqdns = [for record in aws_route53_record.certificate_validation : record.fqdn]

  timeouts {
    create = "30m"
  }
}
