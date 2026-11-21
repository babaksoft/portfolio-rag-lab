#!/usr/bin/env bash

set -euo pipefail

terraform fmt -check -recursive terraform

terraform -chdir=terraform/bootstrap init -backend=false -input=false
terraform -chdir=terraform/bootstrap validate

terraform -chdir=terraform/production init -backend=false -input=false
terraform -chdir=terraform/production validate

echo
echo "Terraform formatting and validation are green."
