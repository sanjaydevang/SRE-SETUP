# SRE And DevOps Study Notes For CRS Lab

These notes explain the tools, architecture, and operations we built in the CRS SRE lab. Use this as your base for hands-on practice first. Later we will convert this into interview scenarios and stories.

Related interview question bank:

```text
docs/interview-prep/SRE-KUBERNETES-INTERVIEW-QUESTION-BANK.md
```

## 1. What We Built

We built a small Central Reservation System lab.

Business flow:

```text
OTA Partner
  |
  v
Reservation Service
  |
  |-- writes reservation to PostgreSQL
  |
  |-- publishes event to Redis Stream
                         |
                         v
              Notification Worker
                         |
                         v
                    Mock PMS
```

This models a real travel/hotel SRE system:

- Booking.com or Expedia sends a reservation.
- Reservation Service validates and confirms the booking.
- Reservation is written to PostgreSQL.
- An event is published to a queue.
- Notification Worker sends the reservation to the hotel's PMS.
- Mock PMS simulates systems like Opera, Protel, Maestro, or other hotel PMS platforms.
- Prometheus scrapes service metrics.
- Grafana visualizes metrics and alerts.
- Splunk-ready logging is configured through structured JSON logs and a Kubernetes Fluent Bit example.

## 2. Repository And GitHub

### What Git Does

Git tracks code changes locally.

Important commands:

```bash
git status
git add .
git commit -m "message"
git log
git diff
git push
git pull
```

### What GitHub Does

GitHub stores your code remotely and supports collaboration.

GitHub gives you:

- remote repository
- branches
- pull requests
- code review
- GitHub Actions CI/CD
- issue tracking
- release history

### What We Did

We created a local git repo for this lab, committed the baseline, and pushed it to:

```text
https://github.com/sanjaydevang/SRE-SETUP
```

Current workflow:

```bash
git status
git add .
git commit -m "Describe the change"
git push
```

### Interview Explanation

> I use Git for local version control and GitHub for remote collaboration. For production work, I create a branch, make a focused change, push it to GitHub, and open a pull request. The pull request triggers CI checks such as tests, linting, Docker build validation, and sometimes deployment checks before the change is merged.

## 3. Application Services

### Reservation Service

Location:

```text
services/reservation_service
```

Purpose:

- accepts reservation requests
- validates payload
- writes reservation to PostgreSQL
- publishes reservation event to Redis Stream
- exposes health and metrics endpoints

Important endpoints:

```text
GET  /health/live
GET  /health/ready
GET  /metrics
POST /v1/reservations
GET  /v1/reservations/{confirmation_id}
```

SRE meaning:

- `/health/live` tells whether the process is alive.
- `/health/ready` tells whether service dependencies are ready.
- `/metrics` exposes Prometheus metrics.

### Notification Worker

Location:

```text
services/notification_worker
```

Purpose:

- reads reservation events from Redis Stream
- sends reservation notification to Mock PMS
- retries failed deliveries
- sends exhausted failures to DLQ
- exposes delivery metrics

Important operational behavior:

- if PMS returns 401, worker logs failure
- if PMS is slow, worker times out
- if PMS returns HTTP 200 but says `stored=false`, worker treats it as business failure
- after max retries, message goes to DLQ

### Mock PMS

Location:

```text
services/mock_pms
```

Purpose:

- simulates a hotel PMS integration
- stores successful reservation notifications
- lets us inject realistic PMS failures

Failure modes:

```text
normal
slow
unauthorized
silent_failure
server_error
```

Set failure mode:

```bash
curl -s -X POST http://localhost:9000/admin/failure-mode \
  -H "Content-Type: application/json" \
  -d '{"mode":"unauthorized"}'
```

Reset:

```bash
curl -s -X POST http://localhost:9000/admin/failure-mode \
  -H "Content-Type: application/json" \
  -d '{"mode":"normal"}'
```

## 4. Docker

### What Docker Does

Docker packages an application and its runtime into an image.

Image:

> A build artifact containing application code, dependencies, and runtime instructions.

Container:

> A running instance of an image.

Dockerfile:

> Instructions for building an image.

### What Docker Solves

Without Docker:

- app works on one laptop but fails elsewhere
- dependencies are manually installed
- deployment environments drift

With Docker:

- repeatable runtime
- consistent packaging
- easier local development
- easier Kubernetes deployment

### Dockerfiles In This Lab

Each service has a Dockerfile:

```text
services/reservation_service/Dockerfile
services/notification_worker/Dockerfile
services/mock_pms/Dockerfile
```

Each Dockerfile does roughly:

1. start from Python image
2. copy requirements
3. install dependencies
4. copy app code
5. run service

### Useful Docker Commands

Build and run all services:

```bash
docker compose up --build
```

Run with observability:

```bash
docker compose -f docker-compose.yml -f docker-compose.observability.yml up --build
```

See running containers:

```bash
docker ps
```

See Compose services:

```bash
docker compose ps
```

View logs:

```bash
docker compose logs reservation-service
docker compose logs notification-worker
docker compose logs mock-pms
```

Stop:

```bash
docker compose down
```

Stop observability stack:

```bash
docker compose -f docker-compose.yml -f docker-compose.observability.yml down
```

### Interview Explanation

> Docker gives us consistent packaging. I can build each service into an image and run the same runtime locally, in CI, or in Kubernetes. When troubleshooting containers, I check container status, logs, environment variables, ports, health checks, and whether dependent services are reachable.

## 5. Docker Compose

### What Docker Compose Does

Docker Compose runs multiple containers together.

In our lab, Compose starts:

- PostgreSQL
- Redis
- Reservation Service
- Notification Worker
- Mock PMS
- Prometheus
- Grafana

Main file:

```text
docker-compose.yml
```

Observability file:

```text
docker-compose.observability.yml
```

### Why We Use Two Compose Files

App only:

```bash
docker compose up --build
```

App plus monitoring:

```bash
docker compose -f docker-compose.yml -f docker-compose.observability.yml up --build
```

This keeps your laptop lighter when you only want to test the app.

### Compose Networking

Inside Docker Compose, containers talk using service names:

```text
postgres:5432
redis:6379
mock-pms:9000
reservation-service:8000
notification-worker:8100
```

Example:

```text
DATABASE_URL=postgresql://crs:crs_password@postgres:5432/crs
PMS_BASE_URL=http://mock-pms:9000
```

### Interview Explanation

> Docker Compose is useful for local integration testing. It lets me run the application, database, cache, worker, and observability stack together. It is not usually the production orchestrator, but it is excellent for local development and learning service dependencies.

## 6. PostgreSQL

### What PostgreSQL Does

PostgreSQL is the transactional database.

In our lab, it stores confirmed reservations.

Reservation Service writes to PostgreSQL before publishing an event.

### Operational Checks

Container health check:

```bash
pg_isready -U crs -d crs
```

SRE concerns:

- connection failures
- connection pool exhaustion
- slow queries
- disk usage
- replication lag in production
- backup and restore

### Interview Explanation

> PostgreSQL is the source of truth for reservation data. For incidents, I would check database connectivity, connection count, query latency, locks, CPU, memory, disk, and recent schema or config changes.

## 7. Redis Stream

### What Redis Does In This Lab

Redis is used as a queue through Redis Streams.

Reservation Service publishes:

```text
reservation-events
```

Notification Worker consumes from:

```text
reservation-events
```

Failed messages go to:

```text
reservation-events-dlq
```

### Why Async Queue Matters

Without queue:

- reservation request waits for PMS
- if PMS is slow, customer booking is slow
- if PMS is down, reservation may fail

With queue:

- booking can be confirmed quickly
- PMS delivery happens asynchronously
- failures can retry
- DLQ preserves failed messages for investigation

### Interview Explanation

> The queue decouples the customer-facing booking path from third-party PMS delivery. If the PMS is slow or unavailable, the reservation API can still process bookings while the worker retries delivery. DLQ gives us a controlled place to inspect failed events.

## 8. CI/CD

### What CI Means

CI means Continuous Integration.

When a developer commits or opens a pull request, CI runs checks automatically.

Common CI checks:

- unit tests
- integration tests
- linting
- static analysis
- dependency checks
- Docker image build
- security scan
- Terraform validation

### What CD Means

CD can mean Continuous Delivery or Continuous Deployment.

Continuous Delivery:

> Pipeline prepares a release, but human approval is needed for production.

Continuous Deployment:

> Pipeline automatically deploys after checks pass.

### What Our Current GitHub Actions CI Does

File:

```text
.github/workflows/ci.yml
```

Current triggers:

```yaml
on:
  pull_request:
  push:
    branches:
      - main
```

This means CI runs when:

- code is pushed to `main`
- pull request is opened or updated

Current job:

```text
python-tests
```

Current steps:

1. checkout code
2. set up Python 3.12
3. install dependencies
4. install pytest
5. run tests with `pytest -q`

Current test:

```text
tests/test_models.py
```

It validates that a reservation request model accepts a valid payload.

### What We Have Not Automated Yet

We have not yet automated:

- Docker image build in CI
- Docker image push to registry
- Kubernetes deployment
- Terraform plan/apply
- smoke test after deployment
- Grafana dashboard deployment through CI
- Splunk config deployment through CI

Right now, those are manual operations.

### What A Full CI/CD Pipeline Would Do

Developer flow:

```text
Developer changes code
  |
  v
git commit
  |
  v
git push
  |
  v
GitHub Actions starts
  |
  v
Run tests
  |
  v
Build Docker images
  |
  v
Scan images
  |
  v
Push images to registry
  |
  v
Deploy to dev Kubernetes
  |
  v
Run smoke tests
  |
  v
Require approval for prod
  |
  v
Deploy prod
  |
  v
Monitor rollout
```

### Production-Style Pipeline Stages

1. Validate source code
2. Run unit tests
3. Run integration tests
4. Build Docker image
5. Scan Docker image
6. Push image to registry
7. Validate Kubernetes manifests
8. Validate Terraform
9. Deploy to dev
10. Run smoke test
11. Manual approval
12. Deploy to prod
13. Watch rollout status
14. Check metrics after deploy

### Interview Explanation

> CI/CD reduces manual deployment risk. CI catches broken code before merge. CD standardizes deployment steps and can include smoke tests, rollout checks, and rollback. In this lab, we currently run unit tests through GitHub Actions, but deployment is manual. The next step would be extending the pipeline to build Docker images, push them to a registry, deploy to Kubernetes, and run smoke tests.

## 9. Kubernetes

### What Kubernetes Does

Kubernetes orchestrates containers.

It handles:

- scheduling pods
- restarting failed containers
- service discovery
- rolling deployments
- scaling
- ConfigMaps
- Secrets
- health probes
- resource requests and limits

### Main Kubernetes Objects

Namespace:

> Logical environment boundary.

Deployment:

> Desired state for running pods.

Pod:

> Smallest runnable unit in Kubernetes.

Service:

> Stable network endpoint for pods.

ConfigMap:

> Non-secret configuration.

Secret:

> Sensitive configuration.

Readiness probe:

> Should this pod receive traffic?

Liveness probe:

> Should Kubernetes restart this container?

### Kubernetes Files In This Lab

App manifests:

```text
deploy/kubernetes/base
```

Observability:

```text
deploy/kubernetes/observability
```

Splunk:

```text
deploy/kubernetes/splunk
```

### Deploy App To Kubernetes

First build local images:

```bash
./scripts/build-local-images.sh
```

Then apply manifests:

```bash
kubectl apply -f deploy/kubernetes/base
```

Check pods:

```bash
kubectl get pods -n crs-lab
```

Check services:

```bash
kubectl get svc -n crs-lab
```

Watch:

```bash
kubectl get pods -n crs-lab -w
```

### Port Forward

Reservation Service:

```bash
kubectl port-forward -n crs-lab svc/reservation-service 8000:8000
```

Mock PMS:

```bash
kubectl port-forward -n crs-lab svc/mock-pms 9000:9000
```

Prometheus:

```bash
kubectl port-forward -n crs-lab svc/prometheus 9090:9090
```

Grafana:

```bash
kubectl port-forward -n crs-lab svc/grafana 3000:3000
```

### Kubernetes Troubleshooting Commands

```bash
kubectl get pods -n crs-lab
kubectl describe pod -n crs-lab <pod-name>
kubectl logs -n crs-lab deploy/reservation-service
kubectl logs -n crs-lab deploy/notification-worker
kubectl get events -n crs-lab --sort-by=.lastTimestamp
kubectl rollout status -n crs-lab deploy/reservation-service
kubectl rollout undo -n crs-lab deploy/reservation-service
```

### Interview Explanation

> Kubernetes manages the desired state of the application. I define Deployments, Services, ConfigMaps, Secrets, health probes, and resource limits. During incidents, I check pod status, events, logs, service endpoints, readiness probes, resource pressure, and recent rollouts.

## 10. Observability

### What Observability Means

Observability helps answer:

```text
What is happening?
Why is it happening?
Where is the failure?
Who is impacted?
```

Three main signals:

- metrics
- logs
- traces

This lab includes metrics and logs. We have not added tracing yet.

### Metrics

Metrics are numeric time-series data.

Examples:

```text
reservations created
PMS delivery failures
DLQ messages
service uptime
```

Metrics are good for:

- dashboards
- alerting
- trends
- SLOs

### Logs

Logs are event records.

Our services write JSON logs like:

```json
{
  "service": "notification-worker",
  "event": "pms_delivery_failed",
  "confirmation_id": "CRS-123",
  "error": "PMS returned HTTP 401"
}
```

Logs are good for:

- debugging
- root cause analysis
- tracking one request or reservation
- evidence package during escalation

### Traces

Traces show one request across multiple services.

We did not add traces yet, but in production you might use:

- OpenTelemetry
- Jaeger
- Zipkin
- Datadog APM
- AppDynamics

### Interview Explanation

> Metrics tell me something is wrong. Logs help explain what happened. Traces show where time was spent across service hops. For this CRS system, I monitor reservation success, PMS delivery success, failures, DLQ messages, queue health, and dependency readiness.

## 11. Prometheus

### What Prometheus Does

Prometheus collects metrics by scraping HTTP endpoints.

Our services expose metrics at:

```text
reservation-service:8000/metrics
notification-worker:8100/metrics
mock-pms:9000/metrics
```

### Local Docker Prometheus Config

File:

```text
observability/prometheus/prometheus.yml
```

It contains scrape targets:

```yaml
scrape_configs:
  - job_name: reservation-service
    metrics_path: /metrics
    static_configs:
      - targets:
          - reservation-service:8000
```

### Check Prometheus

Open:

```text
http://localhost:9090
```

Targets page:

```text
http://localhost:9090/targets
```

Targets should be UP:

```text
reservation-service
notification-worker
mock-pms
```

### Useful Prometheus Queries

Reservations:

```promql
crs_reservations_created_total
```

Reservation rate:

```promql
rate(crs_reservations_created_total[1m])
```

PMS delivery success:

```promql
crs_pms_delivery_success_total
```

PMS delivery failures:

```promql
crs_pms_delivery_failure_total
```

DLQ messages:

```promql
crs_dlq_messages_total
```

New DLQ messages in last 5 minutes:

```promql
sum(increase(crs_dlq_messages_total[5m])) or vector(0)
```

### Why Use `increase` For Alerts

`crs_dlq_messages_total` is a counter.

Counters only go up. If you alert on:

```promql
crs_dlq_messages_total > 0
```

the alert stays firing forever after the first DLQ message.

Better:

```promql
increase(crs_dlq_messages_total[5m]) > 0
```

This means:

> Alert only if new DLQ messages appeared in the last 5 minutes.

### Interview Explanation

> Prometheus scrapes metrics from service endpoints. In Kubernetes, Prometheus can discover pods using annotations and scrape `/metrics`. I use PromQL to query counters, rates, increases, and SLO-style signals.

## 12. Scraping Metrics From Kubernetes Pods

### How Scraping Works

Each app pod has annotations:

```yaml
annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "8000"
  prometheus.io/path: /metrics
```

Prometheus Kubernetes service discovery finds pods with:

```text
prometheus.io/scrape=true
```

Then it scrapes:

```text
http://pod-ip:port/metrics
```

### Kubernetes Prometheus Config

File:

```text
deploy/kubernetes/observability/01-prometheus.yaml
```

Important config:

```yaml
kubernetes_sd_configs:
  - role: pod
    namespaces:
      names:
        - crs-lab
```

Relabeling keeps only annotated pods.

### How To Verify

Port forward Prometheus:

```bash
kubectl port-forward -n crs-lab svc/prometheus 9090:9090
```

Open:

```text
http://localhost:9090/targets
```

You should see pods for:

```text
reservation-service
notification-worker
mock-pms
```

### Scraping Metrics From Instances

For VM or EC2 instance metrics, common tools are:

- Node Exporter for Linux host metrics
- CloudWatch Agent for AWS metrics
- cAdvisor for container metrics

Example Prometheus scrape for an instance:

```yaml
scrape_configs:
  - job_name: node-exporter
    static_configs:
      - targets:
          - server1.example.com:9100
          - server2.example.com:9100
```

### Interview Explanation

> For Kubernetes workloads, I usually scrape pod metrics through service discovery and annotations or ServiceMonitor objects if using Prometheus Operator. For VM-based systems, I install exporters such as Node Exporter and configure Prometheus to scrape instance endpoints.

## 13. Grafana

### What Grafana Does

Grafana visualizes metrics from Prometheus.

Prometheus stores/query metrics.

Grafana displays:

- dashboards
- graphs
- stat panels
- alert rules
- notification routing

### Local Grafana

Open:

```text
http://localhost:3000
```

Login:

```text
admin / admin
```

Dashboard:

```text
Dashboards -> CRS SRE Lab -> CRS SRE Overview
```

### Grafana Files

Datasource provisioning:

```text
observability/grafana/provisioning/datasources/prometheus.yml
```

Dashboard provisioning:

```text
observability/grafana/provisioning/dashboards/dashboards.yml
```

Dashboard JSON:

```text
observability/grafana/dashboards/crs-overview.json
```

### Dashboard Panels We Created

The dashboard shows:

- Reservations Created
- Reservation API Errors
- PMS Delivery Success
- DLQ Messages
- Reservation Rate
- PMS Delivery Rate

### How To Create A Dashboard Manually

1. Open Grafana.
2. Go to Dashboards.
3. Click New dashboard.
4. Add visualization.
5. Choose Prometheus datasource.
6. Enter PromQL query.
7. Pick visualization type.
8. Save dashboard.

Example panel query:

```promql
sum(rate(crs_reservations_created_total[1m]))
```

### Interview Explanation

> Grafana dashboards help operators quickly understand system health. For this CRS system, I build panels around the user journey: reservation traffic, error rate, PMS delivery success, PMS delivery failures, and DLQ messages.

## 14. Grafana Alerts

### What Alerts Do

Alerts notify engineers when a condition is bad.

Good alerts should be:

- actionable
- tied to user impact
- not too noisy
- routed to correct team
- supported by a runbook

### DLQ Alert Example

Alert name:

```text
CRS PMS DLQ Messages Detected
```

Query:

```promql
sum(increase(crs_dlq_messages_total[5m])) or vector(0)
```

Reduce:

```text
Function: Last
```

Threshold:

```text
Is above 0
```

Evaluation:

```text
Every 30s
Pending period: 1m
```

Labels:

```text
service=notification-worker
severity=critical
system=crs
team=sre
```

Summary:

```text
Reservation notification events reached DLQ
```

Description:

```text
PMS delivery failed after retries and one or more messages were sent to DLQ. Check notification-worker logs, PMS credentials, PMS latency, and replay safety.
```

### Why DLQ Alert Matters

DLQ means:

- message failed after retries
- PMS did not receive booking notification
- customer booking may be confirmed in CRS but missing from PMS
- Tier 1 hotel impact could become P1

### Alert Setup Steps

1. Open Grafana.
2. Go to Alerting.
3. New alert rule.
4. Choose Prometheus.
5. Use query:

```promql
sum(increase(crs_dlq_messages_total[5m])) or vector(0)
```

6. Click Run queries.
7. Reduce expression: Last.
8. Threshold: above 0.
9. Folder: CRS SRE Lab.
10. Evaluation group: crs-sre-alerts.
11. Interval: 30s.
12. Pending period: 1m.
13. Add labels.
14. Add summary and description.
15. Save.

### Trigger Alert

Set PMS unauthorized:

```bash
curl -s -X POST http://localhost:9000/admin/failure-mode \
  -H "Content-Type: application/json" \
  -d '{"mode":"unauthorized"}'
```

Create reservation:

```bash
./scripts/smoke-test.sh
```

Watch alert:

```text
Normal -> Pending -> Firing
```

Reset PMS:

```bash
curl -s -X POST http://localhost:9000/admin/failure-mode \
  -H "Content-Type: application/json" \
  -d '{"mode":"normal"}'
```

### Interview Explanation

> I alert on DLQ growth rather than raw failures because DLQ indicates retries were exhausted and manual action may be required. I use `increase` over a time window so the alert fires only for new DLQ events, not forever after an old event.

## 15. Splunk

### What Splunk Does

Splunk stores and searches logs.

In production, logs help answer:

- which reservation failed?
- which hotel chain is affected?
- which PMS endpoint is failing?
- when did failure start?
- what error messages are most common?

### Current Lab Logging

Our app writes JSON logs to stdout.

Examples:

```text
reservation_created
pms_delivery_success
pms_delivery_failed
message_sent_to_dlq
```

### Why stdout Logs Are Correct

In containers, apps should write logs to stdout/stderr.

Then platform-level agents collect logs.

In Kubernetes, log agents collect:

```text
/var/log/containers/*.log
```

### Splunk Kubernetes Configuration

Location:

```text
deploy/kubernetes/splunk
```

We added a Fluent Bit DaemonSet example.

Fluent Bit:

- runs on each Kubernetes node
- reads container logs
- enriches logs with Kubernetes metadata
- sends logs to Splunk HEC

### Splunk HEC

HEC means HTTP Event Collector.

It lets agents send events to Splunk over HTTP.

You need:

- Splunk HEC host
- HEC port, usually `8088`
- HEC token
- Splunk index

### Splunk Config In This Lab

File:

```text
deploy/kubernetes/splunk/00-fluent-bit-splunk.yaml
```

Before applying, replace:

```text
splunk.example.com
replace-with-your-token
```

Do not apply it unless you have a real Splunk HEC endpoint and token.

### Useful SPL Searches

Reservation created:

```spl
index=crs_lab service=reservation-service event=reservation_created
```

PMS failures:

```spl
index=crs_lab service=notification-worker event=pms_delivery_failed
| stats count by error
```

Trace one reservation:

```spl
index=crs_lab confirmation_id="CRS-..."
| table _time service event confirmation_id property_id hotel_tier error
```

Find affected properties:

```spl
index=crs_lab event=pms_delivery_failed
| stats count by hotel_chain_id property_id error
| sort -count
```

Find credential failures:

```spl
index=crs_lab service=notification-worker event=pms_delivery_failed error="*401*"
| stats count by property_id hotel_chain_id
```

### Interview Explanation

> The services emit structured JSON logs to stdout. In Kubernetes, a log forwarder such as Fluent Bit runs as a DaemonSet, collects container logs, enriches them with pod metadata, and forwards them to Splunk HEC. During incidents, I search by confirmation ID, property ID, hotel chain, service, event, and error message.

## 16. Failure Injection Scenarios

### Scenario 1: PMS Unauthorized

Inject:

```bash
curl -s -X POST http://localhost:9000/admin/failure-mode \
  -H "Content-Type: application/json" \
  -d '{"mode":"unauthorized"}'
```

Create reservation:

```bash
./scripts/smoke-test.sh
```

Expected:

- reservation is created
- worker fails PMS delivery
- DLQ increases after retries
- Grafana alert can fire

SRE explanation:

> PMS returned 401, so I suspect credential rotation or secret mismatch. I would check worker logs, confirm scope, validate the Kubernetes Secret or secret manager value, coordinate with integration team, update credentials through change process, and replay DLQ messages if safe.

### Scenario 2: PMS Slow

Inject:

```bash
curl -s -X POST http://localhost:9000/admin/failure-mode \
  -H "Content-Type: application/json" \
  -d '{"mode":"slow"}'
```

Expected:

- worker HTTP timeout
- retry
- DLQ after max attempts

SRE explanation:

> The PMS response time is slower than our worker timeout. I would compare vendor latency with configured timeout, check recent latency trend, and decide whether to tune timeout, add vendor-specific settings, or escalate to PMS vendor.

### Scenario 3: Silent PMS Failure

Inject:

```bash
curl -s -X POST http://localhost:9000/admin/failure-mode \
  -H "Content-Type: application/json" \
  -d '{"mode":"silent_failure"}'
```

Expected:

- PMS returns HTTP 200
- body says `stored=false`
- worker treats it as failure

SRE explanation:

> HTTP 200 does not always mean the business operation succeeded. For PMS integrations, I validate response body and confirm the reservation appears in the destination PMS during onboarding.

### Scenario 4: Redis Down

Stop Redis:

```bash
docker compose stop redis
```

Expected:

- reservation service readiness fails
- queue publish fails
- worker cannot consume events

SRE explanation:

> Redis is the queue dependency. I would check service readiness, queue publish errors, Redis health, and whether an outbox pattern is needed to prevent DB writes and queue events from drifting.

## 17. End-To-End Daily Practice

Start app with observability:

```bash
docker compose -f docker-compose.yml -f docker-compose.observability.yml up --build
```

Run smoke test:

```bash
./scripts/smoke-test.sh
```

Check metrics:

```bash
curl http://localhost:8000/metrics
curl http://localhost:8100/metrics
curl http://localhost:9000/metrics
```

Open:

```text
http://localhost:9090/targets
http://localhost:3000
```

Inject failure:

```bash
curl -s -X POST http://localhost:9000/admin/failure-mode \
  -H "Content-Type: application/json" \
  -d '{"mode":"unauthorized"}'
```

Create booking:

```bash
./scripts/smoke-test.sh
```

Check logs:

```bash
docker compose logs notification-worker
```

Reset:

```bash
curl -s -X POST http://localhost:9000/admin/failure-mode \
  -H "Content-Type: application/json" \
  -d '{"mode":"normal"}'
```

Stop:

```bash
docker compose -f docker-compose.yml -f docker-compose.observability.yml down
```

## 18. What To Say In Interviews

Short architecture answer:

> I built a CRS lab where a reservation API writes bookings to Postgres and publishes events to Redis Stream. A notification worker asynchronously delivers bookings to a PMS integration. I added Docker Compose for local runtime, Kubernetes manifests for deployment, Prometheus metrics, Grafana dashboards and alerts, and Splunk-ready structured logging.

CI/CD answer:

> The current GitHub Actions pipeline runs tests on push and pull request. A production pipeline would also build Docker images, scan them, push to a registry, deploy to Kubernetes, run smoke tests, and monitor rollout health. Right now deployment is manual, which is intentional for learning the DevOps operations step by step.

Observability answer:

> I expose `/metrics` from each service and scrape them with Prometheus. Grafana dashboards show reservation count, PMS delivery success/failure, and DLQ messages. Alerts are configured on DLQ growth using `increase` so they fire only when new failed messages appear.

Splunk answer:

> The application emits structured JSON logs to stdout. In Kubernetes, a Fluent Bit DaemonSet can collect container logs, enrich them with pod metadata, and forward them to Splunk HEC. During incidents, I search by confirmation ID, property ID, hotel chain, event name, and error message.

Incident answer:

> If PMS delivery fails, I check Grafana for DLQ and failure metrics, Prometheus for rate changes, and logs for error details. I scope the blast radius by hotel chain and property, identify whether the issue is credential, timeout, server error, or silent failure, then coordinate mitigation and replay if safe.
