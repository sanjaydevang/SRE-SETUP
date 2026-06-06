#!/usr/bin/env bash
set -euo pipefail

mode="${1:-unauthorized}"
count="${2:-3}"
base_url="${PMS_BASE_URL:-http://127.0.0.1:9000}"

case "$mode" in
  normal|slow|unauthorized|silent_failure|server_error)
    ;;
  *)
    echo "Mode must be normal, slow, unauthorized, silent_failure, or server_error." >&2
    exit 1
    ;;
esac

curl --fail --silent --show-error \
  -X POST "${base_url}/admin/failure-mode" \
  -H "Content-Type: application/json" \
  -d "{\"mode\":\"${mode}\"}"
echo

if [ "$mode" = "normal" ]; then
  echo "PMS reset to normal."
  exit 0
fi

echo "Creating ${count} reservations while PMS mode is ${mode}."
"$(dirname "$0")/demo-generate-traffic.sh" "$count" 0.2
echo "Wait for retries and inspect worker logs, Prometheus alerts, and the DLQ panel."

