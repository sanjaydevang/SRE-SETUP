# Learning Guide

Use this lab in three modes:

1. Implementer: understand what the application does
2. DevOps engineer: package, deploy, and automate it
3. SRE: observe, break, troubleshoot, and explain it

## Application Flow

When you call `POST /v1/reservations`, the reservation service does this:

1. validates the JSON request
2. creates a confirmation ID
3. writes the reservation to PostgreSQL
4. publishes a reservation event to Redis Stream
5. returns HTTP 201 to the caller

The notification worker does this:

1. reads reservation events from Redis Stream
2. sends each event to the mock PMS API
3. retries failed deliveries
4. sends exhausted failures to a DLQ stream
5. exposes metrics for success, failure, and DLQ count

The mock PMS does this:

1. accepts reservation notifications
2. stores successful reservations in memory
3. lets you simulate real PMS failure modes

## Code To Understand First

Start with these files:

- `services/reservation_service/app/main.py`
- `services/notification_worker/app/main.py`
- `services/mock_pms/app/main.py`
- `docker-compose.yml`

## Interview Explanation: Simple Version

> This lab models a hotel CRS. The reservation API accepts a booking, persists it in Postgres, and publishes an event to Redis Stream. A separate notification worker consumes that event and delivers it to a mock PMS. This async design decouples the customer booking path from slower third-party PMS delivery. If the PMS is slow or down, the reservation API can still confirm the booking while the worker retries and eventually sends failed messages to a DLQ.

## SRE Concepts Inside This App

### Health Checks

`/health/live` answers: is the process alive?

`/health/ready` answers: can this service receive traffic right now?

For Kubernetes:

- liveness probe should call `/health/live`
- readiness probe should call `/health/ready`

### Metrics

Each service exposes `/metrics` in Prometheus text format.

Important metrics:

- reservation created count
- reservation error count
- queue publish error count
- PMS delivery success count
- PMS delivery failure count
- DLQ message count

### Logs

The services write structured JSON logs.

Example log event:

```json
{
  "service": "reservation-service",
  "event": "reservation_created",
  "confirmation_id": "CRS-ABC123",
  "property_id": "DAL-100",
  "hotel_tier": "tier1"
}
```

This is how you explain Splunk-style troubleshooting:

> I search logs by `confirmation_id`, `property_id`, `hotel_chain_id`, and error event. That lets me trace one booking from API creation to PMS delivery.

## Failure Scenarios To Practice

### Scenario 1: PMS Credential Rotated

Set failure mode:

```bash
curl -s -X POST http://localhost:9000/admin/failure-mode \
  -H "Content-Type: application/json" \
  -d '{"mode":"unauthorized"}'
```

Expected behavior:

- worker logs `pms_delivery_failed`
- delivery failure metric increases
- after retries, message goes to DLQ

Interview answer:

> I would check whether failures are isolated to one hotel chain or all PMS integrations. Then I would group worker logs by status code. If I see 401s for one PMS endpoint, I suspect credential rotation or secret mismatch. I would validate the secret, confirm with the hotel integration team, update the credential through the approved process, then replay DLQ messages if idempotency allows.

### Scenario 2: PMS Is Slow

Set failure mode:

```bash
curl -s -X POST http://localhost:9000/admin/failure-mode \
  -H "Content-Type: application/json" \
  -d '{"mode":"slow"}'
```

Expected behavior:

- worker timeout occurs because PMS takes longer than the configured timeout
- messages retry
- DLQ increases after max attempts

Interview answer:

> I would compare PMS response latency with the worker timeout. If the PMS normally responds in four or five seconds but the worker timeout is three seconds, we will create false failures. The fix may be timeout tuning, vendor escalation, or separate tier-specific timeout settings.

### Scenario 3: Silent PMS Failure

Set failure mode:

```bash
curl -s -X POST http://localhost:9000/admin/failure-mode \
  -H "Content-Type: application/json" \
  -d '{"mode":"silent_failure"}'
```

Expected behavior:

- PMS returns HTTP 200
- worker still treats it as failed because `stored` is false

Interview answer:

> I do not trust HTTP 200 alone for PMS integrations. Some legacy systems return 200 even when the business operation failed. I validate the response body and, during onboarding, confirm the reservation appears in the destination PMS.

### Scenario 4: Redis Is Down

Stop Redis:

```bash
docker compose stop redis
```

Expected behavior:

- reservation service readiness fails
- queue publish fails
- booking request returns failure after DB write attempt if the queue cannot publish

Interview answer:

> Redis or queue failure affects async delivery. I would check readiness, queue publish errors, and whether we need transactional outbox behavior so DB writes and queue events cannot drift.

## DevOps Work You Should Do Next

### Docker

1. Build images
2. Run `docker compose up --build`
3. Check logs
4. Run smoke test
5. Break one dependency and recover

### GitHub

1. Initialize git
2. Commit this baseline
3. Create a branch for Kubernetes manifests
4. Open a pull request
5. Add CI evidence in the PR description

### Kubernetes

Create manifests for:

- reservation service Deployment and Service
- notification worker Deployment and Service
- mock PMS Deployment and Service
- ConfigMaps
- Secrets
- readiness/liveness probes

### Terraform

Create modules for:

- queue
- database
- redis
- service deployment variables
- hotel onboarding config
- alert thresholds

### CI/CD

Extend `.github/workflows/ci.yml` to:

- run tests
- build Docker images
- run Trivy or another image scanner
- deploy to dev
- run `scripts/smoke-test.sh`

## First Interview Practice Question

Question:

> How would you onboard a new hotel chain into this CRS platform?

Answer:

> I would collect the hotel chain ID, property IDs, tier, PMS endpoint, auth method, timeout expectation, and escalation contacts. Then I would add the hotel config through a controlled PR. Infrastructure modules would create or update queue routing, DLQ thresholds, dashboards, and alerts based on tier. After deployment, I would create test reservations for sample properties, confirm DB writes, confirm queue events, confirm worker delivery, and verify the booking appears inside the PMS. I would also test failure modes like malformed payload, unauthorized PMS, timeout, and silent failure before go-live.

