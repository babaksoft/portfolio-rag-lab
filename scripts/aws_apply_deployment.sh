#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 SAVED_PLAN IMMUTABLE_TAG" >&2
  exit 2
fi

saved_plan=$1
image_tag=$2
terraform_root=${PORTFOLIO_RAG_TERRAFORM_ROOT:-terraform/production}
aws_region=${PORTFOLIO_RAG_AWS_REGION:-us-east-1}
cluster=${PORTFOLIO_RAG_ECS_CLUSTER:-portfolio-rag-production}
service=${PORTFOLIO_RAG_ECS_SERVICE:-portfolio-rag-production}

if [[ $image_tag == latest ]] || [[ ! $image_tag =~ ^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$ ]]; then
  echo "IMMUTABLE_TAG must be a valid Docker tag other than 'latest'." >&2
  exit 2
fi

previous_task_definition=$(aws ecs describe-services \
  --region "$aws_region" \
  --cluster "$cluster" \
  --services "$service" \
  --query 'services[0].taskDefinition' \
  --output text)

rollback() {
  echo "Deployment failed; restoring $previous_task_definition." >&2
  aws ecs update-service \
    --region "$aws_region" \
    --cluster "$cluster" \
    --service "$service" \
    --task-definition "$previous_task_definition" \
    --query 'service.taskDefinition' \
    --output text >&2
  aws ecs wait services-stable \
    --region "$aws_region" \
    --cluster "$cluster" \
    --services "$service"
}

if ! terraform -chdir="$terraform_root" apply -input=false "$saved_plan"; then
  rollback
  exit 1
fi

if ! ./scripts/aws_verify_deployment.sh "$image_tag"; then
  rollback
  exit 1
fi
