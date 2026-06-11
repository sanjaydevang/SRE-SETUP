# Enterprise SRE, DevOps And Cloud Mastery

This curriculum builds production-level understanding for SRE, DevOps, cloud, platform, Kubernetes, infrastructure, and production-support roles.

The objective is not to memorize definitions. For every topic, you should be able to:

- explain the business and technical problem
- place the component in an enterprise architecture
- describe internal behavior and data flow
- identify failure modes
- troubleshoot with evidence
- restore service safely
- prevent recurrence
- explain the topic naturally for 5-10 minutes

## The Production Learning Framework

Every topic follows this sequence:

```text
1. Purpose
2. Architecture
3. Internal behavior
4. Data flow
5. Dependencies
6. Observability
7. Failure modes
8. Troubleshooting
9. Mitigation and recovery
10. Prevention
11. Business impact
12. Interview explanation
13. Hands-on exercise
14. Production scenario
```

## The Incident Reasoning Framework

During troubleshooting, use:

```text
Symptom
  -> Scope
  -> Timeline
  -> Recent changes
  -> Hypotheses
  -> Evidence
  -> Constrained layer
  -> Mitigation
  -> Recovery validation
  -> Root cause
  -> Prevention
```

### Symptom

What is externally visible?

```text
High latency
5xx errors
Connection failures
Pod Pending
Disk full
Queue backlog
Missing batch output
Authentication failure
```

### Scope

```text
One user or all users?
One service or entire platform?
One node or every node?
One region or multiple regions?
One deployment version or all versions?
One dependency or complete transaction path?
```

### Timeline

```text
When did it start?
Was it sudden or gradual?
Did it align with a deployment?
Does it occur only during peak traffic?
Has it happened before?
```

### Hypotheses

Do not run commands randomly. Each command should validate or reject a hypothesis.

Example:

```text
Hypothesis: CPU saturation is causing latency.
Evidence: CPU usage, run queue, throttling, process CPU.

Hypothesis: Database wait is causing latency.
Evidence: connection wait, query latency, locks, pool utilization.

Hypothesis: External dependency is slow.
Evidence: trace span duration, timeout errors, dependency metrics.
```

## Restoration Priorities

During an outage:

```text
1. Protect people and data
2. Stop impact from increasing
3. Restore critical customer functionality
4. Preserve evidence
5. Validate recovery
6. Determine root cause
7. Prevent recurrence
```

Mitigation is not always root-cause correction.

Examples:

```text
Restart service = mitigation
Fix connection leak = permanent correction

Increase disk = mitigation
Implement retention = permanent correction

Rollback = mitigation and sometimes full correction
Add tests/canary = prevention
```

## Mastery Tracks

### Track 1: Linux And Systems

1. CPU troubleshooting
2. Memory troubleshooting
3. OOM killer and cgroups
4. Disk capacity and I/O latency
5. Inode exhaustion
6. Processes and signals
7. Process states and zombies
8. systemd and `systemctl`
9. `journalctl` and log investigation
10. Linux networking
11. DNS troubleshooting
12. TLS and certificate failures
13. Cron and scheduled jobs
14. Permissions, ownership and ACLs
15. `sudo` and privileged access
16. Package management and patching
17. Boot failures
18. SSH failures

### Track 2: Networking

1. OSI/TCP-IP model in production
2. DNS resolution
3. TCP handshake and resets
4. Connection timeouts
5. Routing
6. NAT
7. Firewalls and security groups
8. Load balancers
9. Proxies
10. TLS
11. HTTP behavior
12. Network latency and packet loss
13. Kubernetes networking
14. CNI
15. NetworkPolicy

### Track 3: Cloud Infrastructure

1. VPC and subnet design
2. Route tables
3. Security groups and NACLs
4. Compute and autoscaling
5. Load balancing
6. Managed databases
7. Object storage
8. IAM
9. Multi-AZ design
10. Multi-region design
11. Cost and capacity
12. Cloud monitoring

### Track 4: Docker

1. Images and layers
2. Containers and namespaces
3. cgroups
4. Networking
5. Volumes
6. Dockerfiles
7. Compose
8. Logging
9. Resource controls
10. Security
11. Registry
12. Troubleshooting

### Track 5: Kubernetes

1. Control plane
2. Scheduler
3. Pods and controllers
4. Deployments
5. Services and ingress
6. ConfigMaps and Secrets
7. Probes
8. Requests and limits
9. Autoscaling
10. Storage
11. Scheduling constraints
12. RBAC
13. Networking
14. Upgrades
15. Cluster failures
16. Workload troubleshooting

### Track 6: Observability

1. Metrics, logs and traces
2. RED and USE methods
3. Prometheus
4. PromQL
5. Grafana
6. Alertmanager
7. Splunk
8. ELK
9. AppDynamics/APM
10. OpenTelemetry
11. SLOs
12. Error budgets
13. Alert design
14. Dashboard design

### Track 7: CI/CD

1. Git workflows
2. Pipeline triggers
3. Build and test stages
4. Artifacts
5. Docker image pipelines
6. Security scans
7. Deployment strategies
8. Kubernetes deployments
9. Approvals
10. Rollbacks
11. GitHub Actions
12. Jenkins

### Track 8: Terraform And IaC

1. Providers and resources
2. Variables and outputs
3. State
4. Modules
5. Remote state
6. Locking
7. Plan/apply
8. Failed applies
9. Drift
10. Import
11. CI/CD integration
12. Security

### Track 9: Messaging

1. Queues and topics
2. Producers and consumers
3. Delivery guarantees
4. Ordering
5. Visibility timeout
6. Retries
7. DLQ
8. Idempotency
9. Backpressure
10. Queue monitoring
11. SQS/SNS
12. Kafka fundamentals

### Track 10: Security

1. IAM
2. Secrets management
3. Credential rotation
4. TLS
5. SSH
6. Service accounts
7. RBAC
8. Network isolation
9. Vulnerability management
10. Image scanning
11. Audit logging
12. Incident response

### Track 11: Databases

1. Connections and pools
2. Query plans
3. Indexes
4. Locks
5. Transactions
6. Replication
7. Backups
8. Failover
9. Capacity
10. Performance troubleshooting

### Track 12: Incident Response

1. Detection
2. Severity
3. Incident command
4. Communication
5. Troubleshooting
6. Mitigation
7. Rollback
8. Recovery validation
9. Postmortems
10. Corrective actions
11. Game days
12. Problem management

### Track 13: High Availability And DR

1. Failure domains
2. Redundancy
3. Health checks
4. Failover
5. RTO and RPO
6. Backups
7. Restore testing
8. Multi-AZ
9. Multi-region
10. Disaster exercises

## Practical Learning Cycle

For every module:

```text
Learn -> Observe -> Break -> Troubleshoot -> Recover -> Explain -> Document
```

Example:

```text
Learn CPU metrics
Observe normal VPS CPU
Generate controlled CPU load
Troubleshoot process and system metrics
Stop the load
Validate recovery
Explain the incident
Write a short postmortem
```

## Interview Answer Structure

For a technical topic:

```text
Definition
Why it exists
Architecture placement
Internal behavior
Failure modes
Troubleshooting
Recovery
Production example
```

For an incident:

```text
Situation
Impact
My responsibility
Evidence
Decision
Mitigation
Validation
Root cause
Prevention
Result
```

## Honesty Standard

Use:

```text
Production experience
Operational support experience
Hands-on lab implementation
Conceptual knowledge
```

Do not combine them.

Example:

> In production, I used Grafana as an operator and added targeted panels. In my personal lab, I built the Prometheus and Grafana stack from scratch.

