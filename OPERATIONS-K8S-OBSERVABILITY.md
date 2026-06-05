# Kubernetes And Observability Operations

Use this guide from the VS Code terminal.

## Path 1: Prometheus And Grafana With Docker Compose

This is the easiest first observability practice.

Start the app plus Prometheus and Grafana:

```bash
docker compose -f docker-compose.yml -f docker-compose.observability.yml up --build
```

Open:

- Reservation API: <http://localhost:8000/docs>
- Prometheus: <http://localhost:9090>
- Grafana: <http://localhost:3000>

Grafana login:

- username: `admin`
- password: `admin`

Run smoke test in a second terminal:

```bash
./scripts/smoke-test.sh
```

In Grafana, open:

```text
Dashboards -> CRS SRE Lab -> CRS SRE Overview
```

Practice:

```bash
curl http://localhost:8000/metrics
curl http://localhost:8100/metrics
curl http://localhost:9000/metrics
```

Interview explanation:

> Each service exposes Prometheus metrics on `/metrics`. Prometheus scrapes those endpoints every 15 seconds. Grafana uses Prometheus as a datasource and visualizes reservation count, PMS delivery success, PMS delivery failures, and DLQ messages.

## Path 2: Kubernetes

Use this after you are comfortable with Docker Compose.

### 1. Enable Kubernetes

In Docker Desktop:

```text
Settings -> Kubernetes -> Enable Kubernetes
```

Then verify:

```bash
kubectl version --client
kubectl cluster-info
```

### 2. Build Local Images

```bash
./scripts/build-local-images.sh
```

The Kubernetes manifests use:

- `crs-sre-lab/reservation-service:local`
- `crs-sre-lab/notification-worker:local`
- `crs-sre-lab/mock-pms:local`

### 3. Deploy The App

```bash
kubectl apply -f deploy/kubernetes/base
```

Watch pods:

```bash
kubectl get pods -n crs-lab -w
```

Check services:

```bash
kubectl get svc -n crs-lab
```

### 4. Deploy Prometheus And Grafana

```bash
kubectl apply -f deploy/kubernetes/observability
```

Check:

```bash
kubectl get pods -n crs-lab
kubectl get svc -n crs-lab
```

### 5. Port Forward Services

Use separate terminals:

```bash
kubectl port-forward -n crs-lab svc/reservation-service 8000:8000
```

```bash
kubectl port-forward -n crs-lab svc/mock-pms 9000:9000
```

```bash
kubectl port-forward -n crs-lab svc/prometheus 9090:9090
```

```bash
kubectl port-forward -n crs-lab svc/grafana 3000:3000
```

Open:

- Reservation API: <http://localhost:8000/docs>
- Prometheus: <http://localhost:9090>
- Grafana: <http://localhost:3000>

### 6. Run Smoke Test Against Kubernetes

Keep reservation-service and mock-pms port-forwards running, then:

```bash
./scripts/smoke-test.sh
```

### 7. Kubernetes Troubleshooting Commands

```bash
kubectl get pods -n crs-lab
kubectl describe pod -n crs-lab <pod-name>
kubectl logs -n crs-lab deploy/reservation-service
kubectl logs -n crs-lab deploy/notification-worker
kubectl logs -n crs-lab deploy/mock-pms
kubectl rollout status -n crs-lab deploy/reservation-service
kubectl get events -n crs-lab --sort-by=.lastTimestamp
```

Interview explanation:

> I first check pod status, events, and logs. Then I check readiness and liveness probes, service endpoints, ConfigMaps, Secrets, and recent rollout history. If a pod is running but not ready, Kubernetes will not route traffic to it through the Service.

## Failure Practice

### PMS Unauthorized

```bash
curl -s -X POST http://localhost:9000/admin/failure-mode \
  -H "Content-Type: application/json" \
  -d '{"mode":"unauthorized"}'
```

Then:

```bash
./scripts/smoke-test.sh
kubectl logs -n crs-lab deploy/notification-worker
```

Explain:

> PMS returned 401, so I checked worker logs and saw delivery failures. I would validate PMS credentials, update the Kubernetes Secret through a controlled deployment, and replay DLQ messages only after confirming idempotency.

### PMS Slow

```bash
curl -s -X POST http://localhost:9000/admin/failure-mode \
  -H "Content-Type: application/json" \
  -d '{"mode":"slow"}'
```

Explain:

> The worker has a 3-second HTTP timeout. The mock PMS sleeps for 5 seconds, so delivery fails and retries. This models a timeout mismatch between a PMS vendor and our notification service.

### Reset PMS

```bash
curl -s -X POST http://localhost:9000/admin/failure-mode \
  -H "Content-Type: application/json" \
  -d '{"mode":"normal"}'
```

## Prometheus Checks

Open Prometheus:

```text
http://localhost:9090
```

Try queries:

```promql
crs_reservations_created_total
```

```promql
crs_pms_delivery_success_total
```

```promql
crs_pms_delivery_failure_total
```

```promql
crs_dlq_messages_total
```

## Splunk

The app writes JSON logs to stdout. That is correct for containers.

For Kubernetes Splunk integration, see:

```text
deploy/kubernetes/splunk
```

Do not apply the Splunk manifest until you have a Splunk HEC endpoint and token.

Useful Splunk searches:

```spl
index=crs_lab service=reservation-service event=reservation_created
```

```spl
index=crs_lab service=notification-worker event=pms_delivery_failed
| stats count by error
```

```spl
index=crs_lab confirmation_id="CRS-..."
| table _time service event confirmation_id property_id hotel_tier error
```

Interview explanation:

> Logs, metrics, and traces answer different questions. Metrics tell me something is wrong, logs explain what happened, and traces show where latency occurred across service hops. In this lab, Prometheus and Grafana cover metrics. Structured JSON logs are Splunk-ready and can be forwarded by Fluent Bit in Kubernetes.

## Cleanup

Docker Compose:

```bash
docker compose -f docker-compose.yml -f docker-compose.observability.yml down
```

Kubernetes:

```bash
kubectl delete namespace crs-lab
```

