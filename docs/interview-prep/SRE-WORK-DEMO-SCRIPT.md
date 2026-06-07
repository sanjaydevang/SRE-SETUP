# SRE Work Demo And Interview Script

This script explains my day-to-day SRE and production-support work, the CRS reservation platform, incident handling, observability, hotel onboarding, automation, release support, security, documentation, and reliability improvements.

The script separates:

- work I performed in production
- work I supported operationally
- hands-on implementations completed in my personal CRS SRE lab

Do not present lab work as production ownership.

---

# 1. Two-Minute Introduction

## Spoken Answer

> My background combines production support, application support, and SRE-style reliability work. At Sabre, I supported a Central Reservation System that connected OTA partners such as Booking.com and Expedia with hotel Property Management Systems.
>
> My responsibilities included P1 and P2 incident response, hotel onboarding validation, PMS delivery monitoring, release support, Splunk investigations, Grafana monitoring, AppDynamics tracing, AWS CloudWatch checks, Jenkins pipeline troubleshooting, server patching, ServiceNow change and incident management, and operational automation.
>
> One of my strongest contributions was improving PMS delivery reliability. I analyzed failures by error category, addressed timeout, credential, and DLQ visibility gaps, and helped improve delivery from 97.2% to 99.6%.
>
> I also automated recurring disk-space incidents, eliminating those incidents for 14 months, and built an AIOps Co-pilot that searched historical RCA documents to reduce incident research time.
>
> To deepen my implementation skills, I built a personal CRS SRE lab using Docker, GitHub Actions, Kubernetes manifests, Prometheus, Grafana, Alertmanager, PostgreSQL, Redis, and structured logging.

---

# 2. System Architecture

## Spoken Answer

> The platform was a Central Reservation System. OTA partners sent availability requests and reservation requests through the ingress layer. The application tier included reservation, availability, pricing, and notification services.
>
> The Reservation Service validated a booking, called supporting services, wrote the confirmed reservation to PostgreSQL, and published an event. The notification flow was asynchronous so that a slow hotel PMS did not block the customer-facing booking response.
>
> Events were routed by hotel tier through SNS and SQS. A Notification Consumer delivered reservations to PMS platforms such as Oracle Opera, Protel, Maestro, and proprietary hotel systems. Failed deliveries were retried and eventually moved to a dead-letter queue.

## Flow

```text
Booking.com / Expedia
        |
        v
Route53 -> WAF -> API Gateway -> ALB
        |
        v
Reservation Service
   |          |             |
   |          |             +--> Rate Calculation Service
   |          +----------------> Availability Service -> Redis
   |
   +--> PostgreSQL
   |
   +--> SNS -> Tier-specific SQS -> Notification Consumer -> Hotel PMS
                                   |
                                   +--> DLQ after retry exhaustion
```

## Applications Supported

```text
Reservation Service
Availability Service
Rate Calculation Service
Notification Consumer
PMS integrations
Customer-facing portal used for smoke tests
Supporting Jenkins deployment pipelines
Integration/application servers
```

## Important Clarification

> I supported these applications from the operational and reliability side. I was not the primary application developer or the owner of the entire AWS/Kubernetes platform.

---

# 3. Reservation Flow

## Spoken Answer

> A reservation request entered through the API layer. The Reservation Service authenticated and validated the request, checked availability, calculated the rate, wrote the confirmed booking to PostgreSQL, and returned an HTTP 201 with a confirmation ID.
>
> It also published a reservation event. SNS routed the event to a tier-specific SQS queue. The Notification Consumer processed it and called the hotel's PMS API. Because this was asynchronous, a temporary PMS problem did not necessarily prevent the customer from receiving a CRS booking confirmation.
>
> Operationally, this created an important reliability risk: a booking could exist in the CRS but be missing from the hotel PMS. That is why PMS delivery success, retries, queue age, and DLQ depth were critical signals.

## End-To-End Validation

```text
1. API returns HTTP 201
2. Confirmation ID is valid
3. Reservation exists in PostgreSQL
4. Event is in the correct tier queue
5. Notification Consumer processes it
6. PMS API receives it
7. Reservation actually appears in PMS
```

---

# 4. Batch And Scheduled Jobs

## Production Examples

The platform included scheduled or asynchronous operational work such as:

```text
Nightly hotel reservation exports to S3
Log archival after retention period
Monthly PMS credential validation
Reservation-event consumers
DLQ processing/replay procedures
Database backups
Release smoke tests
Server patching windows
Disk monitoring cron automation every 15 minutes
```

## Spoken Answer

> In addition to synchronous APIs, the platform had scheduled and asynchronous jobs. Examples included nightly reservation exports, backups, log archival, credential validation, and queue consumers.
>
> For batch jobs I monitored start time, completion status, duration, record count, failure count, last successful execution, dependency availability, and output delivery. A process being alive was not enough; I needed to verify the expected business output was produced.

## Batch Troubleshooting

```text
1. Confirm whether the job started
2. Check scheduler history
3. Check application logs
4. Check input availability
5. Check database and storage connectivity
6. Compare processed record count with baseline
7. Check output file or destination
8. Decide whether rerun is safe
9. Avoid duplicate processing
10. Document recovery
```

---

# 5. Day-To-Day SRE Activities

## Morning Checks

```text
Review overnight P1/P2 incidents
Review PagerDuty alerts and unresolved events
Check ServiceNow priority and aging queues
Review reservation success and latency
Review PMS delivery by hotel tier
Check queue and DLQ depth
Check RDS connections and latency
Check Redis hit rate
Review failed batch jobs
Review recent deployments and changes
Confirm log and monitoring coverage
```

## During The Day

```text
Incident triage
Developer escalation support
Hotel onboarding validation
Monitoring and alert tuning
Release preparation
Runbook updates
Automation work
Problem-management follow-up
Change review
Cross-team coordination
ServiceNow and Confluence documentation
```

## On-Call Work

```text
Acknowledge alerts
Establish incident channel
Scope impact
Collect evidence
Mitigate
Communicate every 10 minutes
Validate recovery
Create incident record
Participate in postmortem
Track corrective actions
```

---

# 6. P1 Incident Response

## First Five Minutes

```text
1. Acknowledge PagerDuty
2. Confirm whether alert is real
3. Open Slack war room or bridge
4. Assign incident commander if required
5. Post initial impact statement
6. Start timeline
7. Check recent changes
8. Scope blast radius
```

## Initial Communication

> We are investigating elevated reservation failures affecting multiple OTA partners. The incident started at approximately 14:05 UTC. The team is checking application health, database connectivity, and recent deployments. The next update will be provided in 10 minutes.

## Scope Questions

```text
One OTA or all OTAs?
One hotel or all hotels?
One tier or all tiers?
One region or all regions?
One endpoint or the entire application?
Only PMS delivery or reservation creation too?
Only new deployments or old instances too?
```

## Layered Troubleshooting

```text
1. User/business symptom
2. DNS/WAF/API Gateway/load balancer
3. Kubernetes pods or application instances
4. Application services
5. Database/cache/queue
6. External PMS
7. Recent change or deployment
```

## Evidence Sources

```text
Grafana: rates, errors, latency, delivery success
Splunk: exception details and affected IDs
AppDynamics: slow service hop and transaction snapshot
CloudWatch: RDS, ALB, SQS, ElastiCache
kubectl: pod status, logs, rollout status
ServiceNow: incident and change history
Jenkins: deployment and pipeline history
```

---

# 7. Rollback Versus Workaround

## When I Push For Rollback

Rollback is preferred when:

```text
The incident started immediately after a deployment
The previous release was stable
The change is reversible
The rollback is tested
Data compatibility is preserved
Rollback is faster than diagnosis
Customer impact is increasing
```

## When I Push For A Workaround

A workaround is preferred when:

```text
Rollback is unsafe
Database migration is not backward compatible
The problem is an external dependency
Only one tenant/hotel is affected
A configuration change can isolate impact
Traffic can be routed away
Capacity can be temporarily increased
The failing feature can be disabled
```

## Decision Statement

> My decision is based on customer impact, confidence in the suspected change, recovery time, data risk, and reversibility. I do not wait for a perfect root cause if a safe mitigation can reduce impact quickly.

## Examples

```text
Bad app/config deployment -> rollback
PMS endpoint unavailable -> retry, queue, isolate, vendor escalation
DB pool exhausted -> temporary pool/capacity mitigation plus config revert
One hotel credential expired -> update credential and replay affected events
Monitoring agent missing -> install agent before release bridge closes
```

---

# 8. Complex P1: Database Connection Pool Exhaustion

## STAR Story

### Situation

> Reservation errors increased to 18%, affecting all OTA partners.

### Task

> I was the first responder responsible for identifying the failing layer, reducing impact, and escalating with evidence.

### Actions

```text
1. Acknowledged PagerDuty
2. Opened incident bridge
3. Confirmed all OTA partners were affected
4. Checked load balancer and pod health
5. Opened AppDynamics transaction traces
6. Found approximately 720 ms waiting for DB connection
7. Confirmed query execution itself was around 28 ms
8. Checked CloudWatch DatabaseConnections
9. Found pool at 100/100
10. Used Splunk to find 4,812 ConnectionPoolTimeoutException events
11. Correlated incident with a recent deployment
12. Identified connectionTimeout=0 configuration
13. Applied temporary capacity mitigation and restarted pods
14. Development team reverted the bad configuration
15. Monitored recovery and error rate
```

### Result

> Root cause was identified in nine minutes. Reservation errors recovered after mitigation and configuration correction.

### Prevention

```text
80% pool utilization alert
DB pool validation in post-deploy checks
CI validation rejecting invalid connectionTimeout
Postmortem and runbook update
```

## Troubleshooting Methodology

> I distinguished connection acquisition time from SQL execution time. That prevented us from blaming slow queries and focused investigation on connection-pool behavior.

---

# 9. Monitoring Healthy But Users Failing

## Spoken Answer

> If monitoring is green but users report failures, I assume we have an observability gap. Infrastructure health does not guarantee business success.

## Investigation

```text
Reproduce the exact user transaction
Identify partner, property, region, and timestamp
Search by confirmation ID or request ID
Check load balancer access logs
Check external dependency responses
Validate response body, not only HTTP code
Check destination system
Compare synthetic test with real user path
Review sampling and dashboard aggregation
```

## Real Example

> A PMS returned HTTP 200 even when it silently dropped reservations. A status-code dashboard looked healthy, but the reservation was absent in the destination PMS. I changed validation to check both transport success and business outcome.

---

# 10. Observability And SLOs

## Service-Level Indicators

### Reservation Service

```text
Successful confirmed reservations / valid reservation attempts
HTTP 5xx rate
p50, p95, and p99 latency
DB connection acquisition time
Dependency error rate
```

### Availability Service

```text
Successful availability responses
p95 and p99 latency
Redis cache hit rate
Database fallback load
```

### PMS Delivery

```text
Successfully stored PMS reservations / delivery attempts
Delivery latency
Retry count
Oldest queue message age
DLQ depth
Failures by hotel tier and error class
```

## SLOs

```text
Tier 1 reservation SLO: 99.95%
Tier 1 PMS delivery SLO: 99.9%
Tier 2 reservation SLO: 99.9%
Tier 2 PMS delivery SLO: 99.5%
Tier 3 reservation SLO: 99.5%
Tier 3 PMS delivery SLO: 99.0%
```

## Error Budget

For a 99.9% monthly SLO:

```text
Allowed failure = 0.1%
Approximate monthly unavailability = 43 minutes
```

For a 99.95% monthly SLO:

```text
Allowed failure = 0.05%
Approximate monthly unavailability = 22 minutes
```

## How Error Budget Is Used

> If the service is consuming error budget too quickly, I reduce release risk, prioritize reliability work, and escalate recurring failure patterns. Error budget connects technical reliability with release decisions.

---

# 11. Establishing Baselines

## Spoken Answer

> I do not choose thresholds from guesswork. I establish baselines using historical data and traffic patterns.

## Method

```text
1. Collect 2-4 weeks of data
2. Separate peak and non-peak traffic
3. Review weekday and weekend behavior
4. Calculate p50, p95, and p99
5. Compare healthy periods with incidents
6. Segment by endpoint, partner, tier, and property
7. Identify seasonality
8. Add safety margin
9. Run new alert in observation-only mode
10. Compare alert results with real incidents
```

## Alert-Tuning Example

> The old error alert used an absolute threshold above 2%. Normal peak baseline was around 1.8%, so it created noise. I ran burn-rate alerts in parallel for 30 days. The old rule fired 18 times, including 15 noise events. The new system fired twice, both real. We then switched to the new model.

---

# 12. Container Logs

## Production Flow

```text
Application writes structured JSON to stdout
Container runtime writes node log files
Filebeat DaemonSet runs on each node
Filebeat collects /var/log/containers logs
Logs are forwarded to Splunk
Splunk indexes fields
Engineers search by correlation identifiers
```

## Important Fields

```text
timestamp
service
environment
level
event
confirmation_id
hotel_chain_id
property_id
hotel_tier
OTA partner
error_class
status_code
latency
trace_id
```

## SPL Examples

```spl
index=crs service=notification-consumer event=pms_delivery_failed
| stats count by hotel_chain_id error_class
```

```spl
index=crs confirmation_id="CRS-123"
| table _time service event property_id status_code error
```

## Spoken Answer

> I used metrics to identify the symptom, logs to identify the failure details, and AppDynamics to locate the slow or failing service hop.

---

# 13. Tool Versions And Vulnerability Management

## Honest Answer About Versions

> I do not quote a production tool version unless I can verify it from the environment or change record. Versions change, and guessing reduces credibility.

## How I Check Versions

```bash
kubectl version
docker version
docker compose version
terraform version
prometheus --version
grafana-server -v
splunk version
```

## Lab Versions

The lab pins versions in Compose, including:

```text
PostgreSQL 16 Alpine
Redis 7 Alpine
Prometheus 2.55.1
Grafana 11.4.0
Node Exporter 1.9.1
cAdvisor 0.49.2
Alertmanager 0.28.1
```

Verify the repository before quoting them because the lab may be upgraded.

## Vulnerability Process

```text
1. Receive CVE/advisory
2. Identify affected package/image/version
3. Determine exploitability and exposure
4. Check vendor fix
5. Test patched version in lower environment
6. Raise change request
7. Capture rollback plan
8. Drain one server/node
9. Patch targeted package
10. Reboot if needed
11. Validate app, logs, sysctl, and monitoring
12. Observe
13. Continue rolling patch
14. Document evidence
```

## Container Security Practices

```text
Pin image versions
Scan images in CI
Use minimal base images
Avoid running as root where practical
Do not store secrets in images
Apply resource limits
Rotate credentials
Patch dependencies
Restrict network exposure
Review SBOM and CVEs
```

---

# 14. Security Contributions And Scenarios

## SSH Tunneling In The Lab

> I configured VPS services to bind to localhost instead of exposing Grafana, Prometheus, Redis, or PostgreSQL publicly. I access them through an encrypted SSH tunnel.

```bash
ssh \
  -L 3000:127.0.0.1:3000 \
  -L 9090:127.0.0.1:9090 \
  <user>@<vps-ip>
```

Benefits:

```text
No public monitoring ports
Traffic encrypted through SSH
Smaller attack surface
Access tied to SSH authentication
```

## TLS Certificate Operations

Use this as knowledge unless you performed it directly in production:

```text
Monitor certificate expiry
Validate full certificate chain
Check hostname/SAN match
Renew before expiry
Deploy to load balancer or ingress
Reload safely
Validate with openssl/curl
Monitor handshake errors
Document rollback
```

Commands:

```bash
openssl s_client -connect api.example.com:443 -servername api.example.com
curl -Iv https://api.example.com
```

## Service Account Lockout Scenario

Do not claim this as a real incident unless it happened.

### Scenario Answer

> If a service account becomes locked, I first determine which services and jobs use it, then check authentication logs for repeated failures. A common cause is an old password remaining in one pod, batch job, or secret after rotation.

```text
1. Scope affected applications
2. Check auth failures and lockout timestamp
3. Identify source hosts/pods
4. Stop repeated bad authentication
5. Unlock or rotate account through approved process
6. Update secret store
7. Restart/reload dependent services
8. Validate authentication
9. Monitor for relock
10. Add expiry and failed-login monitoring
```

## Real Credential Example

> A real PMS reliability issue involved hotels rotating API keys without notifying the integration team. The consumer began receiving 401 responses. We identified the pattern in logs and introduced recurring credential validation and advance expiry checks.

---

# 15. Hotel Onboarding

## Scenario

Assume a new chain called `Hotel X` is onboarding with 300 properties and a REST PMS.

## Step 1: Gather Requirements

```text
Hotel chain ID
Property IDs
Hotel tier
PMS vendor/version
REST or SOAP
Endpoint URLs
Authentication method
Credential owner and rotation process
Expected latency
Rate limits
Maintenance windows
Escalation contacts
Duplicate handling
Idempotency behavior
Required field mappings
Go-live date
```

## Step 2: Configuration And Resource Planning

```text
Add hotel metadata and property mappings
Classify hotel tier
Configure PMS endpoint
Store credentials securely
Configure queue routing
Set retry and timeout policy
Set DLQ threshold
Estimate reservation volume
Review consumer capacity
Create lower-environment test data
```

## Step 3: End-To-End Tests

```text
1. Submit reservation for representative properties
2. Verify HTTP 201
3. Verify confirmation ID
4. Verify PostgreSQL field mapping
5. Verify correct tier queue
6. Verify consumer processing
7. Verify PMS response body
8. Verify reservation appears in PMS
9. Verify cache/inventory behavior
10. Test cancellation or modification if in scope
```

## Step 4: Negative Tests

```text
Invalid property ID
Malformed payload
Expired credential
PMS timeout
HTTP 500
HTTP 200 with business failure
Duplicate reservation
Queue retry
DLQ behavior
Consumer restart during processing
```

## Step 5: Observability

```text
Grafana dashboard filtered by hotel_chain_id
PMS delivery success
PMS latency
Failures by error class
Queue depth and age
DLQ threshold based on tier
Splunk saved searches
PagerDuty routing
Synthetic test reservation
Credential expiry alert
```

## Step 6: Runbook

```text
Architecture and flow
Hotel IDs and PMS endpoint
Authentication owner
Known failure modes
Expected latency
Retry behavior
DLQ replay steps
Escalation contacts
Vendor maintenance process
Rollback plan
Validation queries
```

## Step 7: Go-Live

```text
Approved change
War room
Pre-checks
Controlled enablement
Test booking
PMS confirmation
Dashboard observation
Account manager communication
Post-go-live observation
Change closure
```

## Spoken Answer

> I do not consider onboarding complete when an API returns 200. I verify the complete business outcome in the destination PMS and ensure monitoring, alerting, ownership, and documentation exist before go-live.

---

# 16. Exact Monitoring Added For Hotel X

## Dashboard

```text
Reservation volume
Reservation success rate
PMS delivery rate
PMS latency p95/p99
Failure count by status/error
Queue depth
Oldest message age
DLQ depth
Credential expiry
Properties affected
```

## Alerts

Tier 1:

```text
Any DLQ message -> critical
Delivery SLO burn -> critical
Sustained 401 -> critical
PMS latency above timeout margin -> warning
No successful synthetic booking -> critical
```

Tier 2:

```text
Sustained failure for five minutes
DLQ above calibrated threshold
Delivery SLO burn
```

## Splunk Saved Search

```spl
index=crs hotel_chain_id="HOTEL_X"
| stats count by event error_class property_id
```

---

# 17. Confluence And ServiceNow Documentation

## Confluence Page Structure

```text
1. Service overview
2. Business owner
3. Technical owner
4. Architecture diagram
5. Data flow
6. Dependencies
7. SLO and SLA
8. Dashboards
9. Alert rules
10. Runbooks
11. Hotel onboarding details
12. Known failure modes
13. Escalation contacts
14. Deployment and rollback
15. Batch jobs
16. DR/recovery
17. Change history
```

## What I Update After Onboarding

```text
Property list
PMS endpoint and vendor
Authentication process, without secret value
Timeout and retry settings
Dashboard links
Saved searches
PagerDuty routing
Escalation matrix
Validation evidence
Go-live date
Known limitations
```

## What I Update After An Incident

```text
Incident summary
Timeline
Impact
Root cause
Detection gap
Resolution
Corrective actions
New dashboards/alerts
Runbook corrections
Owner and due date
Links to ServiceNow problem record
```

## ServiceNow

```text
Incident record
Change request
Problem record
Task assignments
Evidence and timestamps
Customer/business impact
Closure validation
Postmortem link
```

---

# 18. Postmortem

## Postmortem Sections

```text
Title and incident ID
Date and duration
Severity
Incident commander
Services affected
Customer/business impact
Detection method
Timeline
Root cause
Contributing factors
What went well
What did not go well
Where we were lucky
Mitigation
Permanent fix
Corrective actions
Owners and deadlines
SLO/error-budget impact
Runbook/dashboard/alert changes
```

## Blameless Language

Avoid:

```text
Engineer forgot
Team made a mistake
Person caused outage
```

Prefer:

```text
The process allowed...
The validation did not detect...
The system lacked...
The change procedure did not include...
```

## Example Corrective Actions

```text
Add DB pool alert
Add CI validation
Add deployment smoke test
Add PMS credential check
Add DLQ alarm
Add Filebeat validation
Update rollback runbook
Assign owner and due date
```

---

# 19. Automation Contributions

## Disk Automation

### Problem

> Fifteen integration servers experienced recurring disk-full incidents caused by accumulated logs.

### Automation

```text
Python script every 15 minutes
At 80%: compress logs older than seven days
Move logs to archive
At 90%: create ServiceNow ticket
Send Slack before/after usage
Preserve logs for RCA
```

### Result

```text
Zero disk-full P2 incidents for 14 months
8-10 engineering hours recovered monthly
Historical logs remained available
```

## AIOps Co-Pilot

```text
Python/FastAPI
FAISS vector store
LangChain
Llama 3 for private deployment
500+ RCA documents
Top similar incidents
86% top-three root-cause retrieval benchmark
Triage research reduced to under five minutes
GitHub Actions pipeline authored
```

## Other Automation/Improvements

```text
Monthly PMS credential validation
DLQ alerting
ServiceNow SLA dashboard
Splunk saved searches
Smoke-test scripts
Health-check scripts
VPS deployment scripts in personal lab
```

---

# 20. Release And Deployment Support

## Pre-Release

```text
Review change ticket
Confirm approvals
Review rollback
Confirm monitoring
Capture baseline
Confirm dependencies
Prepare test data
```

## Post-Deploy Smoke Test

```text
Login
Search availability
Apply promotion
Create dummy booking
Verify database write
Verify inventory/cache update
Verify PMS notification
Verify logs from new instances
Compare errors and p99 latency with baseline
```

## Blue-Green Example

> During a blue-green cutover, I noticed log volume from green instances was missing. Filebeat had not been installed. I raised it before the bridge closed, and logging was restored before the release was considered complete.

---

# 21. Jenkins And CI/CD Support

## Failures Handled

```text
Missing ECR IAM permission
Docker socket permission
Missing environment variables
Staging seed data missing
Build node disk full from image layers
```

## Classification Method

```text
Code failure -> developer
Pipeline configuration -> operations/DevOps
Environment failure -> operations
Infrastructure/IAM -> infrastructure team with exact diagnosis
```

## Honest Ownership

> In production, I diagnosed Jenkins pipeline failures but did not design the entire Jenkins architecture. I authored GitHub Actions for my AIOps Co-pilot and built CI workflows in my personal lab.

---

# 22. Team Size And Scale

Only quote numbers you can verify.

Known scale:

```text
200+ hotel chains/customers on platform
Multiple OTA partners
Three hotel tiers
15 servers covered by disk automation
PMS vendors including Opera, Protel, Maestro
```

Team size is not documented in the source notes.

Use:

> I worked in a cross-functional model with application support, SRE/platform, development, DBA, network, hotel integration, account management, and vendor teams. I do not want to guess the exact total team size, but during an incident the active responders were selected based on the failing layer.

If you know the real number, replace this with it.

---

# 23. Short Day-In-The-Life Demo

## Spoken Script

> I start by reviewing overnight incidents, alert history, ServiceNow queues, reservation success, PMS delivery, queue depth, database connections, and recent changes.
>
> During the day, I may validate a hotel onboarding, troubleshoot a developer pipeline issue, tune an alert, update a runbook, support a release, or automate a recurring task.
>
> If a P1 occurs, I acknowledge it, open the incident bridge, scope the blast radius, check recent changes, and troubleshoot from user symptom through infrastructure and dependencies. I communicate every ten minutes, mitigate quickly, and then validate recovery using both technical health and a complete booking transaction.
>
> Afterward, I document the timeline and root cause, update Confluence and ServiceNow, and track corrective actions such as alerting, CI checks, or automation.

---

# 24. Five-Minute Interview Version

> I supported Sabre's Central Reservation System, which connected OTA partners to hotel PMS platforms. My focus was operational reliability: incident response, hotel onboarding, PMS delivery, observability, release validation, pipeline support, patching, and automation.
>
> For incidents, I followed a layered approach. I scoped partner and hotel impact, checked Grafana and CloudWatch for symptoms, Splunk for exceptions, AppDynamics for the failing service hop, and recent deployments for correlation. I prioritized mitigation, using rollback when a reversible deployment caused impact and workaround when the issue involved an external PMS or unsafe rollback.
>
> My strongest reliability result was improving PMS delivery from 97.2% to 99.6%. I broke failures into timeout, authentication, and DLQ categories, then targeted each category with retry improvements, credential validation, and DLQ monitoring.
>
> I also automated recurring disk incidents across 15 servers, eliminating them for 14 months, supported production releases with end-to-end booking smoke tests, and built an AIOps Co-pilot for historical incident research.
>
> I measure reservation success, latency, PMS delivery success, queue age, DLQ depth, database connections, cache hit rate, and infrastructure health against tier-based SLOs. I document onboarding, incidents, runbooks, dashboards, and corrective actions in Confluence and ServiceNow.

---

# 25. Claims Checklist

## Safe Production Claims From The Source Notes

```text
Used Grafana, Splunk, AppDynamics, CloudWatch, PagerDuty, ServiceNow
Performed P1/P2 first response
Performed hotel onboarding validation
Supported releases
Troubleshot Jenkins pipelines
Coordinated patching
Automated disk monitoring
Built ServiceNow dashboard
Built AIOps Co-pilot
Operationally used kubectl
Improved PMS delivery metrics
Tuned alerts using parallel observation
```

## Present As Lab Experience

```text
Built Prometheus/Grafana stack from scratch
Authored Kubernetes manifests
Built Alertmanager routing
Built Docker Compose observability stack
Implemented VPS SSH tunneling
Created exporters and demo alerts
Created Terraform learning modules when completed
```

## Do Not Claim Without Evidence

```text
Owned enterprise Kubernetes control plane
Designed all Jenkins pipelines
Authored production Terraform modules
Managed production Istio
Managed a specific number of clusters/nodes
Handled a service-account lockout incident
Owned production TLS PKI
Used specific production versions that cannot be verified
```

