#!/usr/bin/env bash
set -euo pipefail

action="${1:-start}"
duration="${DEMO_DURATION_SECONDS:-240}"
container_name="crs-cpu-demo"

case "$action" in
  start)
    docker rm -f "$container_name" >/dev/null 2>&1 || true
    workers="$(nproc)"
    echo "Starting ${workers} CPU workers for ${duration} seconds."
    docker run -d \
      --name "$container_name" \
      --label com.docker.compose.service=cpu-demo \
      alpine:3.21 \
      sh -c "i=0; while [ \$i -lt ${workers} ]; do yes > /dev/null & i=\$((i+1)); done; sleep ${duration}" \
      >/dev/null
    echo "Watch the VPS CPU dashboard. Stop early with: $0 stop"
    ;;
  stop)
    docker rm -f "$container_name" >/dev/null 2>&1 || true
    echo "CPU demo stopped."
    ;;
  *)
    echo "Usage: $0 start|stop" >&2
    exit 1
    ;;
esac

