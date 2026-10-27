#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

COMPOSE_FILE="${COMPOSE_FILE:-${DEPLOY_DIR}/compose.prod.yml}"
ENV_FILE="${ENV_FILE:-${DEPLOY_DIR}/.env}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1/health}"
WAIT_TIMEOUT="${WAIT_TIMEOUT:-120}"

compose=(
  docker compose
  --env-file "${ENV_FILE}"
  -f "${COMPOSE_FILE}"
)

show_diagnostics() {
  exit_code=$?

  trap - ERR

  echo "Deployment failed with exit code ${exit_code}."

  timeout 15 "${compose[@]}" ps || true

  timeout 15 "${compose[@]}" \
    logs --tail=100 postgres api nginx || true

  exit "${exit_code}"
}

trap show_diagnostics ERR

command -v docker >/dev/null
command -v curl >/dev/null

test -r "${COMPOSE_FILE}"
test -r "${ENV_FILE}"

echo "Validating production Compose configuration..."
"${compose[@]}" config --quiet

echo "Pulling production images..."
"${compose[@]}" pull postgres api nginx

echo "Starting PostgreSQL..."
"${compose[@]}" up \
  -d \
  --wait \
  --wait-timeout "${WAIT_TIMEOUT}" \
  postgres

echo "Applying database migrations..."
"${compose[@]}" \
  --profile tools \
  run --rm migrate

echo "Starting API and Nginx..."
"${compose[@]}" up \
  -d \
  --wait \
  --wait-timeout "${WAIT_TIMEOUT}" \
  --remove-orphans \
  api nginx

echo "Checking public application health..."
curl \
  --fail \
  --silent \
  --show-error \
  --retry 12 \
  --retry-connrefused \
  --retry-delay 5 \
  "${HEALTH_URL}" \
  >/dev/null

"${compose[@]}" ps

echo "Deployment completed successfully."
