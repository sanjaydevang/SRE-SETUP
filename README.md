# CRS SRE Lab

This is a hands-on SRE interview practice application based on a hotel Central Reservation System.

You can use it to practice:

- Docker and Docker Compose
- GitHub commits and pull requests
- Kubernetes deployments
- Terraform module design
- CI/CD pipelines
- Observability with logs, metrics, health checks, queues, and failure scenarios
- Incident response storytelling

For Kubernetes, Prometheus, Grafana, and Splunk practice, use:

- `OPERATIONS-K8S-OBSERVABILITY.md`
- `docs/SRE-DEVOPS-STUDY-NOTES.md`
- `deploy/kubernetes/base`
- `deploy/kubernetes/observability`
- `deploy/kubernetes/splunk`

## Architecture

```text
OTA / Client
    |
    v
Reservation Service
    |
    |-- writes reservation --> PostgreSQL
    |
    |-- pushes event --------> Redis Stream
                                  |
                                  v
                         Notification Worker
                                  |
                                  v
                              Mock PMS
```

## Services

### reservation-service

Accepts reservation requests from OTA partners such as Booking.com or Expedia.

Important endpoints:

- `GET /health/live`
- `GET /health/ready`
- `GET /metrics`
- `POST /v1/reservations`
- `GET /v1/reservations/{confirmation_id}`

### notification-worker

Reads reservation events from Redis Stream and delivers them to the PMS.

Important SRE behavior:

- retries failed delivery
- sends exhausted messages to a DLQ stream
- logs structured JSON
- exposes health and metrics

### mock-pms

Simulates a hotel Property Management System.

Important endpoints:

- `GET /health/live`
- `GET /health/ready`
- `GET /metrics`
- `POST /pms/reservations`
- `GET /pms/reservations/{confirmation_id}`
- `POST /admin/failure-mode`

Failure modes:

- `normal`: PMS accepts reservations
- `slow`: PMS responds slowly
- `unauthorized`: PMS returns 401
- `silent_failure`: PMS returns HTTP 200 but does not store reservation
- `server_error`: PMS returns 500

## Run Locally

```bash
docker compose up --build
```

Run locally with Prometheus and Grafana:

```bash
docker compose -f docker-compose.yml -f docker-compose.observability.yml up --build
```

Create a reservation:

```bash
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
```

Check PMS received it:

```bash
curl -s http://localhost:9000/pms/reservations/<confirmation_id>
```

Simulate PMS credential failure:

```bash
curl -s -X POST http://localhost:9000/admin/failure-mode \
  -H "Content-Type: application/json" \
  -d '{"mode":"unauthorized"}'
```

## What To Practice

### Docker

- Build each image
- Inspect logs
- Stop Postgres and observe readiness failure
- Stop Redis and observe reservation queue failure
- Change env vars and restart services

### Kubernetes

Create Deployments, Services, ConfigMaps, Secrets, readiness probes, liveness probes, and resource limits for each service.

Practice:

- `kubectl get pods`
- `kubectl describe pod`
- `kubectl logs`
- `kubectl exec`
- `kubectl rollout status`
- `kubectl rollout undo`

### Terraform

Create modules for:

- network
- database
- redis or queue
- Kubernetes namespace
- service deployment
- observability alerts

Use variables for new hotel onboarding:

- `hotel_chain_id`
- `property_ids`
- `hotel_tier`
- `pms_endpoint`
- `dlq_threshold`
- `pagerduty_policy`

### CI/CD

Start with `.github/workflows/ci.yml`.

Extend it later to:

- build Docker images
- push to registry
- run Terraform validation
- deploy to Kubernetes
- run smoke tests

## Interview Story

Use this system to explain:

> A booking enters the CRS through the reservation API. The service validates the request, writes the confirmed reservation to Postgres, then publishes an event to a queue. The notification worker asynchronously delivers the booking to the hotel PMS. We monitor API error rate, p95/p99 latency, DB health, queue lag, DLQ depth, and PMS delivery success rate by hotel tier. For Tier 1 hotels, DLQ depth greater than zero is treated as high priority because missing PMS delivery affects revenue and guest experience.
