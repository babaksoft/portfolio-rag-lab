#!/usr/bin/env bash

set -euo pipefail

: "${AWS_REGION:?AWS_REGION is required}"
: "${GOOGLE_CLIENT_ID:?GOOGLE_CLIENT_ID is required}"
: "${SECRET_ARN:?SECRET_ARN is required}"
: "${USER_POOL_ID:?USER_POOL_ID is required}"

secret_document="$(
  aws secretsmanager get-secret-value \
    --region "${AWS_REGION}" \
    --secret-id "${SECRET_ARN}" \
    --query SecretString \
    --output text
)"

google_client_secret="$(
  SECRET_DOCUMENT="${secret_document}" python3.12 -c \
    'import json, os; print(json.loads(os.environ["SECRET_DOCUMENT"])["google_oauth_client_secret"])'
)"
unset secret_document

operation="create-identity-provider"
if aws cognito-idp describe-identity-provider \
  --region "${AWS_REGION}" \
  --user-pool-id "${USER_POOL_ID}" \
  --provider-name Google >/dev/null 2>&1; then
  operation="update-identity-provider"
fi

GOOGLE_CLIENT_SECRET="${google_client_secret}" \
GOOGLE_CLIENT_ID="${GOOGLE_CLIENT_ID}" \
USER_POOL_ID="${USER_POOL_ID}" \
OPERATION="${operation}" \
python3.12 -c '
import json
import os

print(json.dumps({
    "UserPoolId": os.environ["USER_POOL_ID"],
    "ProviderName": "Google",
    **({"ProviderType": "Google"} if os.environ["OPERATION"] == "create-identity-provider" else {}),
    "ProviderDetails": {
        "authorize_scopes": "openid email",
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
    },
    "AttributeMapping": {"email": "email", "username": "sub"},
}))
' | aws cognito-idp "${operation}" \
  --region "${AWS_REGION}" \
  --cli-input-json file:///dev/stdin >/dev/null

unset google_client_secret
echo "Google identity provider reconciled without exposing its client secret."
