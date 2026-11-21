#!/usr/bin/env bash

set -euo pipefail

terraform_root=${PORTFOLIO_RAG_TERRAFORM_ROOT:-terraform/production}
aws_region=${PORTFOLIO_RAG_AWS_REGION:-us-east-1}

cluster_arn=$(terraform -chdir="$terraform_root" output -raw ecs_cluster_arn)
task_definition_arn=$(terraform -chdir="$terraform_root" output -raw migration_task_definition_arn)
subnet_ids=$(terraform -chdir="$terraform_root" output -raw application_subnet_ids_csv)
security_group_id=$(terraform -chdir="$terraform_root" output -raw application_security_group_id)
network_configuration="awsvpcConfiguration={subnets=[$subnet_ids],securityGroups=[$security_group_id],assignPublicIp=DISABLED}"

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
