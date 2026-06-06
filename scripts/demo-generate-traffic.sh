#!/usr/bin/env bash
set -euo pipefail

count="${1:-30}"
delay="${2:-0.5}"
base_url="${CRS_BASE_URL:-http://127.0.0.1:8000}"

echo "Generating ${count} reservations against ${base_url}"

for i in $(seq 1 "$count"); do
  response="$(
    curl --fail --silent --show-error \
      -X POST "${base_url}/v1/reservations" \
      -H "Content-Type: application/json" \
      -d "{
        \"ota_partner\": \"Booking.com\",
        \"hotel_chain_id\": \"hotel_alpha\",
        \"property_id\": \"DAL-$((100 + i % 5))\",
        \"hotel_tier\": \"tier1\",
        \"guest_name\": \"Demo Guest ${i}\",
        \"room_type\": \"KING\",
        \"check_in\": \"2026-07-01\",
        \"check_out\": \"2026-07-03\",
        \"guest_count\": 2,
        \"total_amount\": 420.50
      }"
  )"

  confirmation_id="$(
    python3 -c 'import json,sys; print(json.load(sys.stdin)["confirmation_id"])' <<< "$response"
  )"
  printf "%3s/%s  %s\n" "$i" "$count" "$confirmation_id"
  sleep "$delay"
done

echo "Traffic generation complete."

