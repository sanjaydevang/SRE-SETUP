#!/usr/bin/env bash
set -euo pipefail

docker build -t crs-sre-lab/reservation-service:local services/reservation_service
docker build -t crs-sre-lab/notification-worker:local services/notification_worker
docker build -t crs-sre-lab/mock-pms:local services/mock_pms

echo "Built local Kubernetes images:"
echo "  crs-sre-lab/reservation-service:local"
echo "  crs-sre-lab/notification-worker:local"
echo "  crs-sre-lab/mock-pms:local"

