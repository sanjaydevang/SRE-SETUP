#!/usr/bin/env bash
set -euo pipefail

check_endpoint() {
  local name="$1"
  local url="$2"

  if curl --fail --silent --show-error "$url" >/dev/null; then
    printf "%-24s OK\n" "$name"
  else
    printf "%-24s FAILED\n" "$name"
    return 1
  fi
}

check_endpoint "Reservation live" "http://127.0.0.1:8000/health/live"
check_endpoint "Reservation ready" "http://127.0.0.1:8000/health/ready"
check_endpoint "Notification ready" "http://127.0.0.1:8100/health/ready"
check_endpoint "Mock PMS ready" "http://127.0.0.1:9000/health/ready"
check_endpoint "Prometheus ready" "http://127.0.0.1:9090/-/ready"
check_endpoint "Grafana health" "http://127.0.0.1:3000/api/health"
check_endpoint "Node Exporter" "http://127.0.0.1:9100/metrics"
check_endpoint "cAdvisor" "http://127.0.0.1:8080/healthz"
check_endpoint "Postgres Exporter" "http://127.0.0.1:9187/metrics"
check_endpoint "Redis Exporter" "http://127.0.0.1:9121/metrics"
check_endpoint "Alertmanager" "http://127.0.0.1:9093/-/ready"

echo
docker compose \
  -f docker-compose.yml \
  -f docker-compose.observability.yml \
  ps
