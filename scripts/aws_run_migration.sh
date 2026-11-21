#!/usr/bin/env bash

set -euo pipefail

terraform_root=${PORTFOLIO_RAG_TERRAFORM_ROOT:-terraform/production}
aws_region=${PORTFOLIO_RAG_AWS_REGION:-us-east-1}

if [[ $# -gt 1 ]]; then
  echo "Usage: $0 [IMMUTABLE_TAG]" >&2
  exit 2
fi

image_tag=${1:-}

if [[ -n $image_tag ]] && { [[ $image_tag == latest ]] || [[ ! $image_tag =~ ^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$ ]]; }; then
  echo "IMMUTABLE_TAG must be a valid Docker tag other than 'latest'." >&2
  exit 2
fi

cluster_arn=$(terraform -chdir="$terraform_root" output -raw ecs_cluster_arn)
task_definition_arn=$(terraform -chdir="$terraform_root" output -raw migration_task_definition_arn)
subnet_ids=$(terraform -chdir="$terraform_root" output -raw application_subnet_ids_csv)
security_group_id=$(terraform -chdir="$terraform_root" output -raw application_security_group_id)
network_configuration="awsvpcConfiguration={subnets=[$subnet_ids],securityGroups=[$security_group_id],assignPublicIp=DISABLED}"

if [[ -n $image_tag ]]; then
  account_id=$(aws sts get-caller-identity --query Account --output text --region "$aws_region")
  image="$account_id.dkr.ecr.$aws_region.amazonaws.com/portfolio-rag-api:$image_tag"
  aws ecr describe-images \
    --region "$aws_region" \
    --repository-name portfolio-rag-api \
    --image-ids imageTag="$image_tag" \
    --query 'imageDetails[0].imageDigest' \
    --output text >/dev/null

  task_input=$(mktemp)
  trap 'rm -f "$task_input"' EXIT
  aws ecs describe-task-definition \
    --region "$aws_region" \
    --task-definition "$task_definition_arn" \
    --query taskDefinition \
    --output json \
    | jq --arg image "$image" '
      {
        family,
        taskRoleArn,
        executionRoleArn,
        networkMode,
        containerDefinitions,
        volumes,
        placementConstraints,
        requiresCompatibilities,
        cpu,
        memory,
        runtimePlatform,
        ephemeralStorage
      }
      | .containerDefinitions[0].image = $image
      | with_entries(select(.value != null))
    ' >"$task_input"

  task_definition_arn=$(aws ecs register-task-definition \
    --region "$aws_region" \
    --cli-input-json "file://$task_input" \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text)
  echo "Registered migration task definition for $image."
fi

task_arn=$(aws ecs run-task \
  --region "$aws_region" \
  --cluster "$cluster_arn" \
  --task-definition "$task_definition_arn" \
  --launch-type FARGATE \
  --network-configuration "$network_configuration" \
  --count 1 \
  --query 'tasks[0].taskArn' \
  --output text)

if [[ $task_arn == None ]]; then
  echo "ECS did not start the migration task; inspect the run-task failure response." >&2
  exit 1
fi

echo "Waiting for migration task $task_arn"
aws ecs wait tasks-stopped \
  --region "$aws_region" \
  --cluster "$cluster_arn" \
  --tasks "$task_arn"

exit_code=$(aws ecs describe-tasks \
  --region "$aws_region" \
  --cluster "$cluster_arn" \
  --tasks "$task_arn" \
  --query "tasks[0].containers[?name=='migration'].exitCode | [0]" \
  --output text)

if [[ $exit_code != 0 ]]; then
  stop_reason=$(aws ecs describe-tasks \
    --region "$aws_region" \
    --cluster "$cluster_arn" \
    --tasks "$task_arn" \
    --query 'tasks[0].stoppedReason' \
    --output text)
  echo "Migration failed with exit code $exit_code: $stop_reason" >&2
  exit 1
fi

echo "Migration completed successfully."
