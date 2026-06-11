# P1 Incident Architecture And SRE Stories

These stories demonstrate SRE incident response, observability, rollback judgment, root-cause analysis, and prevention.

Important:

- Use `reservation API` or `transaction API` for the Sabre CRS story.
- Use `payment API` only if you genuinely supported a payment service.
- Do not invent tool versions, traffic volumes, team sizes, or implementation ownership.

---

# Platform Architecture

```text
Users / OTA Partners
Booking.com, Expedia, SiteMinder
              |
              v
        Route53 DNS
              |
              v
 AWS WAF / Rate Limiting
              |
              v
        API Gateway
              |
              v
             ALB
              |
              v
      Kubernetes / EKS
   +----------+-----------+
   |          |           |
   v          v           v
Reservation Availability Rate Calculation
Service     Service      Service
   |          |           |
   |          +--> Redis  |
   |                      |
   +--------> PostgreSQL <-+
   |
   v
SNS -> Tier SQS Queues -> Notification Consumer
                              |
                              v
                       Hotel PMS APIs
                              |
                              v
                             DLQ
```

## Observability Architecture

```text
Application metrics -----> Prometheus -----> Grafana alerts
AWS infrastructure ------> CloudWatch ------> Grafana
Container JSON logs -----> Filebeat --------> Splunk
Application agents ------> AppDynamics ----> Traces/snapshots
Grafana alerts ----------> PagerDuty ------> On-call engineer
Incident records --------> ServiceNow
Communication -----------> Slack war room
Documentation -----------> Confluence
```

## Release Architecture

```text
Developer commit
      |
      v
Jenkins / CI pipeline
      |
      +--> tests
      +--> image/package build
      +--> artifact registry
      +--> deployment
      |
      v
Rolling / Blue-Green Release
      |
      v
Readiness checks -> Smoke test -> Observation window
      |
      +--> Continue
      |
      +--> Roll back
```

---

# Incident 1: P1 5xx Spike After Bad Deployment

## Executive Summary

> Shortly after a production deployment, reservation API 5xx errors increased significantly across multiple OTA partners. I correlated the incident with the deployment, confirmed that the new version was failing while infrastructure remained healthy, recommended rollback, validated recovery, and helped introduce stronger deployment guardrails.

## Normal Request Path

```text
OTA
 |
 v
ALB
 |
 v
Reservation Service pods
 |
 +--> Availability Service
 +--> Rate Calculation Service
 +--> PostgreSQL
 +--> SNS/SQS notification flow
```

## Failure Path

```text
New application version deployed
          |
          v
New pods become available
          |
          v
Requests reach incompatible/bad configuration
          |
          v
Unhandled exception / dependency failure
          |
          v
HTTP 500 responses increase
```

## Detection

Possible initial signals:

```text
PagerDuty page for reservation 5xx rate
Grafana error-rate panel rises
ALB HTTPCode_Target_5XX_Count rises
Splunk shows repeated exception after deployment
AppDynamics reports failed business transactions
Customer/OTA reports booking failures
```

## First Five Minutes

```text
1. Acknowledge PagerDuty
2. Open incident bridge
3. State customer impact
4. Check deployment timestamp
5. Determine affected partners/endpoints
6. Confirm whether old and new versions behave differently
7. Assign application, platform, and database responders
8. Set next communication time
```

Initial communication:

> We are investigating elevated reservation API 5xx responses beginning immediately after the latest production deployment. Multiple OTA partners are affected. The team is validating the new application version and dependencies. The next update will be provided in 10 minutes.

## Troubleshooting Sequence

### 1. Confirm The Symptom

```text
Is it 4xx or 5xx?
Which endpoint?
Which partners?
Which availability zone or pod version?
What percentage of requests?
When did it begin?
```

Prometheus-style query:

```promql
sum(rate(http_requests_total{service="reservation",status=~"5.."}[5m]))
/
sum(rate(http_requests_total{service="reservation"}[5m]))
```

### 2. Correlate With The Deployment

```bash
kubectl rollout history deployment/reservation-service -n <namespace>
kubectl rollout status deployment/reservation-service -n <namespace>
kubectl get pods -n <namespace> -o wide
```

Questions:

```text
Did the alert start after rollout?
Are failures only on the new image?
Did configuration or secrets change?
Did a schema migration occur?
Are readiness probes truly testing dependencies?
```

### 3. Check Infrastructure

```text
ALB healthy targets
Pod readiness
Pod restarts
CPU/memory
Node health
Database availability
Redis and queue health
```

Purpose:

> This separates an application regression from infrastructure failure.

### 4. Inspect Logs

Example Splunk search:

```spl
index=crs service=reservation-service earliest=-15m
| stats count by version error_class message
| sort -count
```

Correlation search:

```spl
index=crs service=reservation-service status>=500
| stats count by pod_name image_version error_class
```

### 5. Inspect Traces

In AppDynamics:

```text
Open failed business transactions
Compare successful and failed snapshots
Identify failing service/backend call
Compare old version and new version
Check exception stack and response time
```

## Rollback Decision

I recommend rollback when:

```text
Impact started immediately after deployment
New version is strongly correlated with failures
Previous version was stable
Rollback artifact is available
Database/event changes are backward compatible
Rollback is faster and safer than a live fix
```

Before rollback:

```text
Confirm no irreversible schema migration
Confirm previous image/config exists
Capture logs and evidence
Notify incident commander
Record rollback decision in timeline
```

Rollback:

```bash
kubectl rollout undo deployment/reservation-service -n <namespace>
kubectl rollout status deployment/reservation-service -n <namespace>
```

For blue-green:

```text
Shift ALB/ingress traffic back to the stable environment.
```

## Recovery Validation

Rollback completion is not sufficient.

```text
5xx rate returns to baseline
p95/p99 latency returns to baseline
Pods are Ready
ALB targets are healthy
Database connections remain stable
Queue backlog does not grow
Reservation smoke test succeeds
PMS receives the test reservation
Logs and traces are present
```

## My Contribution

> As the SRE/operations responder, I acknowledged the incident, established the bridge, scoped the impact, correlated the error spike with the release, compared telemetry across application versions, collected evidence for the application team, recommended rollback based on customer impact and reversibility, monitored rollback, and performed end-to-end validation before declaring recovery.

## Postmortem

### Root Cause Example

Use the actual cause if known. Defensible possibilities include:

```text
Missing environment variable
Invalid connection-pool configuration
Incompatible API contract
Incorrect feature flag
Schema incompatibility
Bad dependency endpoint
Unhandled null/validation condition
```

Do not combine several possible causes in the final story.

### Contributing Factors

```text
Test environment did not reproduce production configuration
Readiness probe checked process health but not dependency readiness
Canary stage was missing
Post-deploy smoke test did not cover the failing path
Alert detected failures only after broad traffic exposure
Configuration validation was incomplete
```

### Corrective Actions

```text
Add pre-deployment configuration validation
Add integration test for failing transaction path
Add canary or progressive delivery
Add automatic rollback criteria
Add deployment annotations to Grafana
Add image version to logs and metrics
Improve readiness checks
Require smoke test before full traffic
Update runbook and rollback checklist
```

## Result Statement

> Rollback restored reservation success and latency to baseline. The postmortem resulted in stronger configuration validation, improved smoke testing, deployment/version visibility, and a safer progressive rollout process.

---

# Incident 2: P1/P2 Transaction API High Latency

## Executive Summary

> During peak traffic, reservation or transaction API latency increased from the normal range into multi-second response times. I used Grafana and AppDynamics to locate the delay, Splunk to identify the error pattern, and CloudWatch/database metrics to confirm connection-pool saturation. I coordinated an immediate mitigation and helped implement preventive monitoring and CI controls.

## Normal Path

```text
Client
  |
  v
API Gateway / ALB
  |
  v
Reservation or Transaction API
  |
  +--> Supporting microservices
  +--> PostgreSQL
  +--> External dependency, if applicable
```

Do not add a payment provider unless it was genuinely part of the application.

## Symptoms

```text
Normal p95: approximately 600-800 ms
Incident p95/p99: several seconds
5xx or timeout errors increase
Connection acquisition time increases
Queueing occurs at application layer
Customer transactions fail or time out
```

## Detection

```text
Latency SLO/burn-rate alert
AppDynamics slow transaction
Grafana p95/p99 increase
Splunk connection timeout exceptions
CloudWatch DatabaseConnections at ceiling
Customer complaints
```

## Investigation

### 1. Scope

```text
All transactions or one API?
All partners or one customer?
All pods or one pod?
All database operations or one query?
Only peak traffic?
Did it start after a change?
```

### 2. RED Metrics

```text
Rate
Errors
Duration
```

Questions:

```text
Did traffic increase?
Did error rate rise?
Did p95/p99 rise while p50 remained normal?
```

### 3. AppDynamics Trace

Example evidence:

```text
DB connection acquisition: 720 ms
Actual SQL execution: 28 ms
```

Interpretation:

> The SQL query was not the primary bottleneck. Requests were waiting for a connection from the application pool.

### 4. Database Metrics

```text
Active connections
Maximum connections
Pool utilization
Connection wait time
Database CPU
Database memory
Lock waits
Query latency
```

### 5. Logs

```spl
index=crs service=reservation-service
"ConnectionPoolTimeoutException"
| timechart count span=1m
```

### 6. Recent Changes

```text
Pool settings
Timeout changes
Replica count
Database configuration
Traffic pattern
Slow query deployment
Connection leak
Dependency latency
```

## Immediate Mitigation Options

### Option A: Traffic Control

```text
Throttle non-critical endpoints
Apply partner rate limits
Disable expensive optional functions
Protect critical reservation traffic
```

Best when:

```text
Database is near capacity
Additional application scaling would increase connections
Traffic can be prioritized safely
```

### Option B: Temporary Pool Increase

Best when:

```text
Database has verified connection headroom
CPU/memory are healthy
The increase is controlled and monitored
```

Risk:

> Increasing the pool without database headroom can move the bottleneck into PostgreSQL and worsen the outage.

### Option C: Roll Back

Best when:

```text
Recent deployment changed pool behavior
Previous configuration was stable
Rollback is backward compatible
```

### Option D: Scale Application

Risk:

```text
More pods multiplied by pool size may create more database connections.
```

Example:

```text
10 pods x 100 connections = 1,000 possible connections
20 pods x 100 connections = 2,000 possible connections
```

## My Decision

> I prioritized protecting the database and reducing user impact. I verified whether the database had connection headroom before changing the pool and avoided blindly adding application replicas. Where possible, non-critical traffic was controlled while engineering corrected the unsafe configuration.

Only mention actual throttling if it happened.

## Recovery Validation

```text
Connection wait time returns to normal
Pool utilization falls below threshold
p95/p99 latency recovers
5xx/timeouts recover
Database CPU remains stable
No lock or query regression
Reservation smoke test succeeds
Queue and PMS delivery remain healthy
```

## My Contribution

> I isolated connection waiting from query execution, correlated traces, logs, and database metrics, provided a specific diagnosis instead of a generic database escalation, supported the mitigation decision, monitored recovery, and converted the incident findings into alerts, deployment checks, and CI controls.

## Postmortem

### Root Cause

Use the verified cause:

```text
Unsafe connection-pool configuration
Connection leak
Slow dependency holding connections
Slow query increasing connection occupancy
Unexpected concurrency
```

### Contributing Factors

```text
No pool-utilization alert
Configuration was not validated in CI
Load test did not reproduce peak concurrency
Scaling model did not account for total connections
Runbook lacked connection-pool checks
```

### Corrective Actions

```text
Alert at 80% pool utilization
Monitor connection acquisition latency
Add CI policy for pool settings
Load test at peak concurrency
Set finite timeouts
Detect connection leaks
Document total connection budget
Add deployment baseline comparison
Add database protection/rate limits
```

## Result Statement

> The mitigation restored transaction latency and reduced errors. The permanent changes improved early detection, prevented unsafe configuration, and made database connection capacity part of deployment and scaling reviews.

---

# SRE Incident Command Model

## Roles

```text
Incident Commander: owns coordination and decisions
Technical Lead: leads diagnosis
Communications Lead: sends stakeholder updates
Scribe: maintains timeline
Application Team: code/config analysis
Platform Team: Kubernetes/load balancer
DBA: database analysis
Vendor Team: external dependency
```

In a small incident, one person may cover multiple roles.

## Communication Cadence

```text
Initial update within 5-10 minutes
Updates every 10-15 minutes
Immediate update for major scope or mitigation change
Recovery update after validation
Final incident summary
```

## Update Template

```text
Impact:
Scope:
Start time:
Current hypothesis:
Actions completed:
Next action:
Next update:
```

---

# Postmortem Template

```text
Incident title and ID
Severity
Date and duration
Customer/business impact
Services affected
Detection
Timeline
Root cause
Contributing factors
Mitigation
Recovery validation
What went well
What did not go well
Where we were lucky
SLO/error-budget impact
Corrective actions
Owners
Due dates
Runbook/dashboard/alert changes
```

## Example Corrective Action Table

| Action | Owner | Priority | Due Date | Verification |
|---|---|---:|---|---|
| Add 80% pool alert | SRE | P1 | Confirmed date | Test alert |
| Add CI config validation | Development | P1 | Confirmed date | Failing pipeline test |
| Add canary release stage | Platform | P2 | Confirmed date | Canary deployment |
| Add deployment markers | Observability | P2 | Confirmed date | Grafana annotation |
| Update rollback runbook | SRE | P2 | Confirmed date | Game-day review |

---

# Demo Architecture Using The CRS Lab

The personal lab can demonstrate both incidents:

```text
Client curl
   |
   v
Reservation Service
   |
   +--> PostgreSQL
   +--> Redis Stream
            |
            v
     Notification Worker
            |
            v
         Mock PMS

Node Exporter ----\
cAdvisor ----------+--> Prometheus --> Grafana
App metrics -------/
                          |
                          v
                     Alertmanager
```

## Demo 1: Simulate Bad Deployment

Safer demonstration:

```text
Stop Reservation Service
Observe target DOWN
Observe alert Pending/Firing
Restart service
Validate smoke test
```

Commands:

```bash
./scripts/demo-stop-service.sh reservation-service 90
```

Explain:

> In a real deployment incident, I would compare versions and roll back. In this lab, stopping the service safely demonstrates detection, notification, and recovery.

## Demo 2: Transaction Dependency Failure

```bash
./scripts/demo-pms-failure.sh unauthorized 3
```

Show:

```text
Reservations remain confirmed
PMS failures increase
Retries occur
DLQ increases
Alert fires
```

Reset:

```bash
./scripts/demo-pms-failure.sh normal
./scripts/smoke-test.sh
```

---

# Interview Answers

## Tell Me About A Bad Deployment

> A production deployment caused a sharp increase in reservation API 5xx responses. I correlated the start time with the rollout, confirmed that infrastructure and dependencies were generally healthy, and used Splunk and AppDynamics to isolate failures to the new version. Because the previous version was stable and rollback was compatible, I recommended rollback rather than attempting an untested production fix. I monitored rollout recovery, validated an end-to-end reservation, and confirmed error rate and latency returned to baseline. The postmortem added configuration validation, stronger smoke tests, deployment markers, and progressive rollout controls.

## Tell Me About High API Latency

> During a P1, reservation latency and errors increased across OTA partners. AppDynamics showed requests waiting approximately 720 milliseconds to acquire a database connection while SQL execution itself was around 28 milliseconds. CloudWatch showed the pool at its ceiling, and Splunk confirmed connection-pool timeout exceptions. I helped apply a controlled mitigation after verifying database headroom, supported correction of the unsafe configuration, and validated recovery. We then added pool-utilization alerting, connection-wait monitoring, CI configuration validation, and load-testing requirements.

## Why Did You Roll Back?

> The timing and version-specific evidence strongly linked the incident to the deployment. The previous version was stable, rollback was reversible, and customer impact was increasing. Rollback had lower risk and a shorter recovery time than debugging or patching live.

## Why Not Scale?

> The bottleneck was database connection capacity. Adding pods could multiply connection pools and worsen database pressure. I first protected the constrained dependency.

## What Did You Change Afterward?

> We improved detection, prevention, and recovery: alerting on early saturation, CI validation, progressive rollout, deployment markers, better smoke tests, and a tested rollback runbook.

