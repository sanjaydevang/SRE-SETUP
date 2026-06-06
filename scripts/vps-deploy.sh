#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

git pull --ff-only
docker compose \
  -f docker-compose.yml \
  -f docker-compose.observability.yml \
  up -d --build --remove-orphans

docker compose \
  -f docker-compose.yml \
  -f docker-compose.observability.yml \
  ps

echo
echo "Deployment complete. Run ./scripts/vps-health-check.sh to verify endpoints."

