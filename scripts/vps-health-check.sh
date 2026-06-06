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
check_endpoint "cAdvisor" "http://127.0.0.1:18080/healthz"
check_endpoint "Alertmanager" "http://127.0.0.1:9093/-/ready"

check_prometheus_target() {
  local job="$1"

  if curl --fail --silent --get \
    --data-urlencode "query=up{job=\"${job}\"}" \
    "http://127.0.0.1:9090/api/v1/query" \
    | python3 -c '
import json
import sys

data = json.load(sys.stdin)
results = data.get("data", {}).get("result", [])
healthy = bool(results) and all(item["value"][1] == "1" for item in results)
raise SystemExit(0 if healthy else 1)
'; then
    printf "%-24s OK\n" "${job} target"
  else
    printf "%-24s FAILED\n" "${job} target"
    return 1
  fi
}

check_prometheus_target "node-exporter"
check_prometheus_target "cadvisor"
check_prometheus_target "postgres-exporter"
check_prometheus_target "redis-exporter"

echo
docker compose \
  -f docker-compose.yml \
  -f docker-compose.observability.yml \
  ps
