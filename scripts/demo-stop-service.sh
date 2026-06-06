#!/usr/bin/env bash
set -euo pipefail

service="${1:-}"
duration="${2:-90}"

case "$service" in
  reservation-service|notification-worker|mock-pms|postgres|redis)
    ;;
  *)
    echo "Usage: $0 reservation-service|notification-worker|mock-pms|postgres|redis [seconds]" >&2
    exit 1
    ;;
esac

compose=(
  docker compose
  -f docker-compose.yml
  -f docker-compose.observability.yml
)

echo "Stopping ${service} for ${duration} seconds."
"${compose[@]}" stop "$service"
echo "Watch Prometheus targets and alerts."
sleep "$duration"
echo "Starting ${service}."
"${compose[@]}" start "$service"
"${compose[@]}" ps "$service"

