#!/usr/bin/env bash
set -euo pipefail

response="$(
  curl -s -X POST http://localhost:8000/v1/reservations \
    -H "Content-Type: application/json" \
    -d '{
      "ota_partner": "Booking.com",
      "hotel_chain_id": "hotel_alpha",
      "property_id": "DAL-100",
      "hotel_tier": "tier1",
      "guest_name": "Devang Patel",
      "room_type": "KING",
      "check_in": "2026-07-01",
      "check_out": "2026-07-03",
      "guest_count": 2,
      "total_amount": 420.50
    }'
)"

echo "$response"
confirmation_id="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["confirmation_id"])' <<< "$response")"

sleep 2
curl -f -s "http://localhost:9000/pms/reservations/${confirmation_id}"
echo
echo "smoke test passed for ${confirmation_id}"
