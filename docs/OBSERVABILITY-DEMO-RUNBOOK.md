# Observability And Alerting Demo Runbook

This runbook teaches how to monitor the Hostinger VPS, containers, application, PostgreSQL, and Redis. It also provides a repeatable real-time demo.

## 1. Observability Architecture

```text
Reservation Service ----\
Notification Worker -----+--> Prometheus --> Grafana dashboards
Mock PMS ---------------/

VPS Linux --> Node Exporter ----/
Docker ----> cAdvisor ----------/
Postgres --> Postgres Exporter -/
Redis ----> Redis Exporter -----/

Prometheus rules --> Alertmanager --> Local webhook receiver
```

### Components

`Node Exporter`

- reads VPS Linux metrics
- CPU
- memory
- disk
- filesystem
- network
- load average

`cAdvisor`

- reads Docker container metrics
- CPU by container
- memory by container
- network by container
- filesystem usage by container

`Postgres Exporter`

- connects to PostgreSQL
- exposes database availability, connections, transactions, and database statistics

`Redis Exporter`

- connects to Redis
- exposes availability, memory, keys, commands, and client statistics

`Prometheus`

- scrapes all `/metrics` endpoints every 15 seconds
- stores time-series data
- evaluates alert rules every 15 seconds

`Grafana`

- queries Prometheus
- displays dashboards
- can also create Grafana-managed alerts

`Alertmanager`

- receives firing alerts from Prometheus
- groups duplicate alerts
- routes notifications
- sends resolved notifications

`Local webhook receiver`

- receives Alertmanager webhook messages
- prints them in Docker logs
- proves that notification routing works without requiring Slack or email credentials

## 2. Deploy The New Monitoring Stack

First push the latest repository changes from the Mac:

```bash
git add .
git commit -m "Add VPS infrastructure monitoring and alert demos"
git push
```

On the VPS:

```bash
cd /opt/apps/SRE-SETUP
git pull --ff-only
```

Deploy:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.observability.yml \
  up -d --build
```

The first deployment downloads:

- Node Exporter
- cAdvisor
- Postgres Exporter
- Redis Exporter
- Alertmanager
- local webhook receiver

Check:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.observability.yml \
  ps
```

Verify:

```bash
./scripts/vps-health-check.sh
```

## 3. SSH Tunnel From The Mac

Run this on the Mac:

```bash
ssh \
  -L 8000:127.0.0.1:8000 \
  -L 8100:127.0.0.1:8100 \
  -L 9000:127.0.0.1:9000 \
  -L 9090:127.0.0.1:9090 \
  -L 9093:127.0.0.1:9093 \
  -L 3000:127.0.0.1:3000 \
  -L 18080:127.0.0.1:18080 \
  -L 9080:127.0.0.1:9080 \
  <user>@<vps-ip>
```

Keep the tunnel terminal open.

Open:

- Grafana: <http://localhost:3000>
- Prometheus: <http://localhost:9090>
- Prometheus targets: <http://localhost:9090/targets>
- Prometheus alerts: <http://localhost:9090/alerts>
- Alertmanager: <http://localhost:9093>
- cAdvisor: <http://localhost:18080>
- API docs: <http://localhost:8000/docs>

## 4. Verify Prometheus Targets

Open:

```text
http://localhost:9090/targets
```

Expected targets:

```text
reservation-service
notification-worker
mock-pms
node-exporter
cadvisor
postgres-exporter
redis-exporter
prometheus
alertmanager
```

Each should show:

```text
State: UP
```

If a target is DOWN:

1. read its Last Error column
2. check the exporter container
3. check container logs
4. test its `/metrics` endpoint

Example:

```bash
docker compose logs --tail=100 node-exporter
curl http://127.0.0.1:9100/metrics
```

## 5. Grafana Dashboards

Open:

```text
http://localhost:3000
```

Navigate:

```text
Dashboards -> CRS SRE Lab
```

Dashboards:

```text
CRS SRE Overview
VPS Infrastructure Overview
```

### Application Dashboard

Panels:

- reservations created
- reservation API errors
- PMS delivery success
- DLQ messages
- reservation rate
- PMS delivery rate

This answers:

```text
Are customers successfully creating reservations?
Are PMS notifications succeeding?
Are failed notifications reaching DLQ?
```

### Infrastructure Dashboard

Panels:

- VPS CPU usage
- VPS memory usage
- root disk usage
- healthy scrape targets
- PostgreSQL availability
- Redis availability
- CPU and memory history
- network throughput
- load average
- container CPU by service
- container memory by service
- PostgreSQL connections
- Redis memory
- scrape target health

This answers:

```text
Is the host healthy?
Which container is consuming resources?
Are data services available?
Is monitoring itself healthy?
```

## 6. Important PromQL Queries

### VPS CPU Usage

```promql
100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[2m])) * 100)
```

Theory:

- CPU exposes cumulative seconds by mode.
- `rate(...[2m])` calculates per-second change.
- idle percentage is subtracted from 100.

### VPS Memory Usage

```promql
(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100
```

Use `MemAvailable`, not only `MemFree`, because Linux uses available memory for filesystem cache.

### Root Disk Usage

```promql
(1 - node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100
```

### Network Receive Rate

```promql
sum(rate(node_network_receive_bytes_total{device!~"lo|veth.*|docker.*|br-.*"}[2m]))
```

### Container CPU

```promql
sum by (container_label_com_docker_compose_service) (
  rate(container_cpu_usage_seconds_total{
    container_label_com_docker_compose_service!=""
  }[2m])
)
```

The value represents CPU cores used:

```text
1.0 = one full CPU core
0.5 = half a CPU core
```

### Container Memory

```promql
sum by (container_label_com_docker_compose_service) (
  container_memory_working_set_bytes{
    container_label_com_docker_compose_service!=""
  }
)
```

### PostgreSQL

Availability:

```promql
pg_up
```

Connections:

```promql
sum(pg_stat_activity_count)
```

### Redis

Availability:

```promql
redis_up
```

Memory:

```promql
redis_memory_used_bytes
```

### Target Health

```promql
up
```

Prometheus automatically creates `up`:

```text
1 = scrape succeeded
0 = scrape failed
```

## 7. Alert Rules

Rules are stored at:

```text
observability/prometheus/rules/crs-alerts.yml
```

Current alerts:

```text
CRSScrapeTargetDown
CRSDLQMessagesDetected
CRSPMSDeliveryFailures
VPSHighCPU
VPSHighMemory
VPSDiskSpaceLow
VPSFilesystemReadOnly
PostgreSQLExporterDown
PostgreSQLHighConnections
RedisExporterDown
RedisMemoryHigh
```

### Alert Lifecycle

```text
Inactive -> Pending -> Firing -> Resolved
```

`Inactive`

The condition is false.

`Pending`

The condition is true, but the `for` duration has not completed.

`Firing`

The condition stayed true for the required duration.

`Resolved`

The condition became healthy after firing.

### Why Use A Pending Period

Without a pending period, a brief spike creates noise.

Example:

```yaml
expr: CPU > 80
for: 2m
```

This alerts only if CPU remains high for two minutes.

## 8. Alertmanager Routing

Prometheus sends firing alerts to:

```text
alertmanager:9093
```

Alertmanager groups by:

```text
alertname
service
severity
```

It sends the notification to:

```text
alert-receiver:8080/alerts
```

Watch real-time notification payloads:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.observability.yml \
  logs -f alert-receiver
```

When an alert fires, the logs show a JSON webhook payload.

When the alert recovers, Alertmanager sends another payload with:

```json
"status": "resolved"
```

This is a credential-free notification demo.

## 9. Demo 1: Application Traffic

Open:

```text
Grafana -> CRS SRE Overview
```

On the VPS:

```bash
./scripts/demo-generate-traffic.sh 50 0.2
```

Watch:

- Reservations Created increases
- Reservation Rate rises
- PMS Delivery Success increases
- container CPU/network may move

What to say:

> I am generating real API requests. The reservation counter increases, and `rate()` converts the counter into throughput over time. The async worker consumes events and the PMS success metric follows.

## 10. Demo 2: CPU Alert

Open:

```text
Grafana -> VPS Infrastructure Overview
Prometheus -> Alerts
Alertmanager
```

Start:

```bash
./scripts/demo-cpu-load.sh start
```

Watch:

- VPS CPU rises
- load average rises
- `VPSHighCPU` becomes Pending
- after two minutes it becomes Firing
- Alertmanager receives it
- alert receiver logs the notification

Watch notifications:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.observability.yml \
  logs -f alert-receiver
```

Stop:

```bash
./scripts/demo-cpu-load.sh stop
```

The alert eventually resolves.

What to say:

> Node Exporter exposes cumulative CPU time. Prometheus calculates the non-idle rate. The alert requires CPU above 80 percent for two minutes, which prevents brief spikes from paging the team.

## 11. Demo 3: Container Memory

Start:

```bash
DEMO_MEMORY_MB=256 ./scripts/demo-memory-load.sh start
```

Watch:

- VPS memory usage
- memory-demo container series
- cAdvisor metrics

Stop:

```bash
./scripts/demo-memory-load.sh stop
```

Use a smaller value on low-memory VPS instances:

```bash
DEMO_MEMORY_MB=128 ./scripts/demo-memory-load.sh start
```

Do not set a value that could destabilize the VPS.

## 12. Demo 4: Service Down Alert

Open Prometheus Targets and Alerts.

Stop the Reservation Service for 90 seconds:

```bash
./scripts/demo-stop-service.sh reservation-service 90
```

Watch:

- reservation-service target becomes DOWN
- `up{job="reservation-service"}` becomes `0`
- `CRSScrapeTargetDown` becomes Pending, then Firing
- service automatically starts after 90 seconds
- alert resolves

You can repeat with:

```bash
./scripts/demo-stop-service.sh redis 90
./scripts/demo-stop-service.sh postgres 90
```

Stopping Redis or PostgreSQL also affects application readiness.

What to say:

> Prometheus uses the `up` metric to show whether scraping succeeds. A failed scrape may mean the process is down, the network path is broken, or the metrics endpoint is unhealthy. I confirm the cause using container status and logs.

## 13. Demo 5: PMS Failure And DLQ

Open:

```text
Grafana -> CRS SRE Overview
Prometheus -> Alerts
Alertmanager
```

Inject unauthorized responses:

```bash
./scripts/demo-pms-failure.sh unauthorized 3
```

Watch:

- reservations still get confirmed
- worker delivery failures increase
- retries occur
- DLQ increases
- `CRSPMSDeliveryFailures` fires
- `CRSDLQMessagesDetected` fires

Check worker logs:

```bash
docker compose logs --tail=100 notification-worker
```

Reset:

```bash
./scripts/demo-pms-failure.sh normal
```

What to say:

> The customer-facing booking path remains available because PMS delivery is asynchronous. The worker retries, then moves exhausted messages to the DLQ. The alert is tied to operational impact because DLQ means automatic recovery failed.

## 14. Real Notification Options

The local webhook proves routing. For a real environment, configure:

- Slack
- Microsoft Teams
- email
- PagerDuty
- ServiceNow webhook

Recommended learning path:

1. local webhook receiver
2. Grafana contact point to email or Slack
3. Alertmanager Slack/PagerDuty routing
4. severity-based routing

Example routing model:

```text
severity=warning  -> Slack
severity=critical -> PagerDuty
service=database  -> database on-call
service=crs       -> application SRE
```

Never commit webhook URLs, API keys, or tokens to Git. Store them in secrets or environment-specific configuration.

## 15. How To Build A Good Dashboard

Start with questions, not graphs.

### User Experience Row

```text
Request rate
Error rate
Latency
Business success rate
```

### Dependency Row

```text
PostgreSQL
Redis
PMS
Queue and DLQ
```

### Infrastructure Row

```text
CPU
Memory
Disk
Network
Container restarts
```

### Monitoring Health Row

```text
Prometheus targets
Exporter health
Alertmanager health
Scrape duration
```

Avoid dashboards containing many graphs with no operational question.

## 16. Alert Tuning Method

For each alert, define:

```text
What user impact does it represent?
What action should on-call take?
How long should the condition persist?
Which severity is appropriate?
Who owns the service?
What runbook supports it?
```

Tune using:

- historical baseline
- incident history
- SLO/error budget
- pending duration
- grouping
- inhibition
- severity labels

Example:

Bad:

```promql
crs_dlq_messages_total > 0
```

It stays firing after one old message.

Better:

```promql
increase(crs_dlq_messages_total[5m]) > 0
```

It detects only new failures.

## 17. Ten-Minute Demo Sequence

### Minute 0-1: Architecture

Explain exporters, Prometheus, Grafana, Alertmanager.

### Minute 1-3: Baseline

Show:

- Prometheus targets UP
- VPS CPU/memory/disk
- application dashboard

### Minute 3-5: Generate Traffic

```bash
./scripts/demo-generate-traffic.sh 30 0.2
```

Show counters and rates.

### Minute 5-7: PMS Failure

```bash
./scripts/demo-pms-failure.sh unauthorized 3
```

Show worker logs, DLQ, and alerts.

### Minute 7-9: CPU Alert

```bash
./scripts/demo-cpu-load.sh start
```

Explain pending period and Alertmanager routing.

### Minute 9-10: Recovery

```bash
./scripts/demo-pms-failure.sh normal
./scripts/demo-cpu-load.sh stop
```

Show resolved alert and explain mitigation versus root cause.

## 18. Interview Explanation

> I built an observability pipeline for a CRS application on a VPS. Application services expose custom Prometheus metrics. Node Exporter provides host CPU, memory, disk, load, and network metrics. cAdvisor provides container-level resource metrics. Postgres and Redis exporters provide dependency health. Prometheus scrapes all targets every 15 seconds and evaluates alert rules. Grafana provides application and infrastructure dashboards. Alertmanager groups and routes firing and resolved alerts to a webhook receiver, which can later be replaced with Slack, PagerDuty, or ServiceNow.
