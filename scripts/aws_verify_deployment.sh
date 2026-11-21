#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 IMMUTABLE_TAG" >&2
  exit 2
fi

image_tag=$1
aws_region=${PORTFOLIO_RAG_AWS_REGION:-us-east-1}
cluster=${PORTFOLIO_RAG_ECS_CLUSTER:-portfolio-rag-production}
service=${PORTFOLIO_RAG_ECS_SERVICE:-portfolio-rag-production}

if [[ $image_tag == latest ]] || [[ ! $image_tag =~ ^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$ ]]; then
  echo "IMMUTABLE_TAG must be a valid Docker tag other than 'latest'." >&2
  exit 2
fi

aws ecs wait services-stable \
  --region "$aws_region" \
  --cluster "$cluster" \
  --services "$service"

task_arn=$(aws ecs list-tasks \
  --region "$aws_region" \
  --cluster "$cluster" \
  --service-name "$service" \
  --desired-status RUNNING \
  --query 'taskArns[0]' \
  --output text)

if [[ $task_arn == None ]]; then
  echo "The service has no running task." >&2
  exit 1
fi

for container in api ui; do
  repository="portfolio-rag-$container"
  expected_digest=$(aws ecr describe-images \
    --region "$aws_region" \
    --repository-name "$repository" \
    --image-ids imageTag="$image_tag" \
    --query 'imageDetails[0].imageDigest' \
    --output text)
  running_digest=$(aws ecs describe-tasks \
    --region "$aws_region" \
    --cluster "$cluster" \
    --tasks "$task_arn" \
    --query "tasks[0].containers[?name=='$container'].imageDigest | [0]" \
    --output text)
  running_image=$(aws ecs describe-tasks \
    --region "$aws_region" \
    --cluster "$cluster" \
    --tasks "$task_arn" \
    --query "tasks[0].containers[?name=='$container'].image | [0]" \
    --output text)

  if [[ $running_image != *":$image_tag" ]] || [[ $running_digest != "$expected_digest" ]]; then
    echo "$container is not running the expected immutable image: $running_image ($running_digest)." >&2
    exit 1
  fi
done

echo "The production task is healthy and runs both expected image digests for $image_tag."
