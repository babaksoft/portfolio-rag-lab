#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 IMMUTABLE_TAG" >&2
  exit 2
fi

image_tag=$1
aws_region=${PORTFOLIO_RAG_AWS_REGION:-us-east-1}

if [[ $image_tag == latest ]] || [[ ! $image_tag =~ ^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$ ]]; then
  echo "IMMUTABLE_TAG must be a valid Docker tag other than 'latest'." >&2
  exit 2
fi

account_id=$(aws sts get-caller-identity --query Account --output text --region "$aws_region")
registry="$account_id.dkr.ecr.$aws_region.amazonaws.com"

aws ecr get-login-password --region "$aws_region" \
  | docker login --username AWS --password-stdin "$registry"

api_image="$registry/portfolio-rag-api:$image_tag"
ui_image="$registry/portfolio-rag-ui:$image_tag"

docker build --pull --file docker/api.Dockerfile --tag "$api_image" .
docker build --pull --file docker/ui.Dockerfile --tag "$ui_image" .

docker push "$api_image"
docker push "$ui_image"

echo "Published immutable application images:"
echo "  API: $api_image"
echo "  UI:  $ui_image"
echo
echo "Set api_image_tag and ui_image_tag to '$image_tag' in the reviewed Terraform inputs."
