#!/usr/bin/env bash
set -euo pipefail

action="${1:-start}"
memory_mb="${DEMO_MEMORY_MB:-256}"
duration="${DEMO_DURATION_SECONDS:-240}"
container_name="crs-memory-demo"

case "$action" in
  start)
    docker rm -f "$container_name" >/dev/null 2>&1 || true
    echo "Allocating approximately ${memory_mb} MiB for ${duration} seconds."
    docker run -d \
      --name "$container_name" \
      --memory="$((memory_mb + 64))m" \
      --tmpfs "/load:rw,size=${memory_mb}m" \
      --label com.docker.compose.service=memory-demo \
      alpine:3.21 \
      sh -c "dd if=/dev/zero of=/load/demo.bin bs=1M count=${memory_mb} status=none; sleep ${duration}" \
      >/dev/null
    echo "Watch VPS and container memory. Stop early with: $0 stop"
    ;;
  stop)
    docker rm -f "$container_name" >/dev/null 2>&1 || true
    echo "Memory demo stopped."
    ;;
  *)
    echo "Usage: $0 start|stop" >&2
    exit 1
    ;;
esac

