# Linux CPU Troubleshooting

CPU troubleshooting is not simply running `top` and looking for a high percentage. A production engineer must determine:

```text
Is CPU actually the bottleneck?
Is the pressure user CPU, kernel CPU, I/O wait, steal time, or throttling?
Is one process responsible?
Is the issue host-wide or container-specific?
Is high CPU the cause of latency or a symptom of another failure?
What mitigation restores service without creating a second incident?
```

---

# 1. What CPU Represents

The CPU executes instructions for:

- application code
- operating-system kernel work
- networking
- encryption
- compression
- garbage collection
- database processing
- container runtime activity

Linux reports CPU time in several modes.

| Mode | Meaning | Production interpretation |
|---|---|---|
| `us` | User CPU | Application code is consuming CPU |
| `sy` | System CPU | Kernel, networking, system calls |
| `id` | Idle | CPU has no runnable work |
| `wa` | I/O wait | CPU is waiting while I/O completes |
| `st` | Steal | Hypervisor is taking CPU from the VM |
| `hi` | Hardware interrupts | Device interrupt processing |
| `si` | Software interrupts | Often network packet processing |

> [!IMPORTANT]
> High load average does not always mean high CPU. Load includes runnable tasks and tasks blocked in uninterruptible I/O.

---

# 2. Where CPU Fits In Architecture

```text
Customer request
      |
      v
Load balancer
      |
      v
Application process/container
      |
      +--> application instructions use CPU
      +--> TLS encryption uses CPU
      +--> JSON parsing uses CPU
      +--> logging uses CPU
      +--> garbage collection uses CPU
      +--> database client uses CPU
```

CPU pressure can cause:

- increased latency
- request timeouts
- failed health probes
- queue backlog
- thread starvation
- autoscaling
- container throttling
- missed cron schedules
- database slowdown

---

# 3. Production Symptoms

CPU problems may appear as:

```text
p95/p99 latency increase
5xx or timeout errors
Health probes failing
Queue depth increasing
Load average increasing
Pods being throttled
Batch jobs taking longer
SSH becoming slow
Alert processing delayed
```

Do not assume CPU is the root cause because latency and CPU rise together.

Example:

> A retry storm caused by a failing dependency can increase CPU. The dependency failure is the root cause; CPU is a secondary symptom.

---

# 4. First Response Method

Use this order:

```text
1. Confirm customer impact
2. Check system-wide CPU and load
3. Separate CPU modes
4. Identify processes/threads
5. Check memory, I/O and network correlation
6. Check containers/cgroups
7. Check recent changes
8. Mitigate
9. Validate recovery
```

---

# 5. Command: `uptime`

```bash
uptime
```

Example:

```text
14:30:21 up 42 days, 3:18, 4 users, load average: 8.20, 7.95, 6.10
```

Interpretation:

- `8.20`: 1-minute load average
- `7.95`: 5-minute load average
- `6.10`: 15-minute load average

Check CPU count:

```bash
nproc
```

If the server has four CPUs:

```text
Load 4: approximately one runnable/blocked task per CPU
Load 8: approximately two per CPU
```

## Hypothesis Validated

> Is the machine experiencing sustained runnable or I/O-blocked work?

## Limitation

`uptime` does not tell:

- which process
- CPU mode
- whether tasks are waiting on disk
- whether a container is throttled

---

# 6. Command: `top`

```bash
top
```

Key sections:

```text
load average
Tasks
%Cpu(s)
MiB Mem
process list
```

Useful keys:

```text
P  sort by CPU
M  sort by memory
1  show individual CPU cores
H  show threads
c  show full command
```

Example CPU line:

```text
%Cpu(s): 75.0 us, 10.0 sy, 0.0 ni, 10.0 id, 3.0 wa, 0.0 hi, 2.0 si, 0.0 st
```

Interpretation:

```text
75% user CPU: application-heavy workload
10% system CPU: kernel/system-call work
3% I/O wait: limited storage waiting
0% steal: hypervisor is not withholding CPU
```

## Hypothesis Validated

> Is CPU saturated, and which process or thread is consuming it?

---

# 7. Command: `vmstat`

```bash
vmstat 1
```

Important columns:

| Column | Meaning |
|---|---|
| `r` | Runnable processes |
| `b` | Processes blocked on I/O |
| `si` | Swap in |
| `so` | Swap out |
| `in` | Interrupts |
| `cs` | Context switches |
| `us` | User CPU |
| `sy` | System CPU |
| `id` | Idle |
| `wa` | I/O wait |
| `st` | Steal |

Example:

```text
 r  b   swpd   free   si   so   us   sy   id   wa   st
12  0      0 500000    0    0   82   10    8    0    0
```

On a four-core host:

```text
r=12 means many runnable tasks are waiting for four CPUs.
```

Another example:

```text
 r  b   swpd   free   si   so   us   sy   id   wa   st
 1 14      0 500000    0    0    5    3   12   80    0
```

Interpretation:

> The machine is not compute-bound. Many tasks are blocked and I/O wait is 80%. Investigate storage rather than adding CPU.

## Hypotheses Validated

```text
Are tasks waiting for CPU?
Are tasks blocked on I/O?
Is swapping involved?
Is the hypervisor stealing CPU?
```

---

# 8. Command: `mpstat`

Install if needed:

```bash
sudo apt install sysstat
```

Run:

```bash
mpstat -P ALL 1
```

Purpose:

- shows each CPU core
- identifies uneven load
- separates CPU modes

Example:

```text
CPU  %usr  %sys  %iowait  %steal  %idle
0    98.0   1.0      0.0     0.0    1.0
1    20.0   3.0      0.0     0.0   77.0
```

Interpretation:

> One core is saturated while another is mostly idle. The process may be single-threaded or pinned to one CPU.

## Hypothesis Validated

> Is pressure balanced across CPUs, or is a single core the bottleneck?

---

# 9. Command: `pidstat`

```bash
pidstat 1
```

Threads:

```bash
pidstat -t -p <pid> 1
```

Context switches:

```bash
pidstat -w 1
```

I/O:

```bash
pidstat -d 1
```

Purpose:

- process CPU over time
- thread CPU
- voluntary/involuntary context switches
- process I/O

## Hypotheses Validated

```text
Which process is consuming CPU consistently?
Is one application thread hot?
Is excessive context switching occurring?
Is the process actually I/O-heavy?
```

---

# 10. Command: `ps`

Top CPU processes:

```bash
ps -eo pid,ppid,user,stat,%cpu,%mem,etime,cmd --sort=-%cpu | head -20
```

Important columns:

```text
PID      process ID
PPID     parent process
STAT     process state
%CPU     CPU use
ETIME    elapsed runtime
CMD      full command
```

Why `ETIME` matters:

> A newly started process consuming CPU may correlate with a deployment, cron job, or runaway script.

---

# 11. Process States

Common states:

| State | Meaning |
|---|---|
| `R` | Running/runnable |
| `S` | Interruptible sleep |
| `D` | Uninterruptible sleep, often I/O |
| `T` | Stopped |
| `Z` | Zombie |

Find `D` state:

```bash
ps -eo state,pid,ppid,wchan:32,cmd | awk '$1=="D"'
```

Many `D` tasks plus high load may indicate:

- slow disk
- NFS problem
- blocked storage
- kernel/device issue

---

# 12. Check I/O Before Blaming CPU

```bash
iostat -xz 1
```

Important fields:

```text
await      I/O response time
aqu-sz     queue length
%util      device utilization
```

Reason:

> High load and latency may come from storage wait, even when CPU idle remains available.

---

# 13. Check Memory And Swapping

```bash
free -h
vmstat 1
```

Look for:

```text
low MemAvailable
swap-in/swap-out
major page faults
```

Reason:

> Memory pressure can create CPU overhead through reclaim, swapping, and garbage collection.

---

# 14. Check Containers

Docker:

```bash
docker stats --no-stream
```

Inspect resource limits:

```bash
docker inspect <container> \
  --format 'CPUQuota={{.HostConfig.CpuQuota}} Memory={{.HostConfig.Memory}}'
```

Kubernetes:

```bash
kubectl top pods -n <namespace>
kubectl top nodes
kubectl describe pod -n <namespace> <pod>
```

CPU throttling metric:

```promql
rate(container_cpu_cfs_throttled_seconds_total[5m])
```

CPU usage:

```promql
rate(container_cpu_usage_seconds_total[5m])
```

Important:

> A container can have high latency while the host has spare CPU if the container CPU limit is throttling it.

---

# 15. Check Recent Changes

```text
Deployment
Configuration change
Feature flag
Traffic increase
Cron/batch job
Security scan
Backup
Log compression
Certificate operation
Kernel/package update
```

Commands:

```bash
journalctl --since "30 minutes ago"
systemctl list-timers
ps -eo lstart,pid,cmd --sort=-lstart | head
```

Kubernetes:

```bash
kubectl rollout history deployment/<name> -n <namespace>
kubectl get events -n <namespace> --sort-by=.lastTimestamp
```

---

# 16. Common CPU Failure Patterns

## Pattern A: Legitimate Traffic Surge

Evidence:

```text
Request rate rises
CPU rises proportionally
Errors/latency rise after capacity limit
No unusual process
```

Mitigation:

```text
Scale replicas/nodes
Apply rate limits
Prioritize critical traffic
Enable caching
```

Prevention:

```text
Capacity testing
Autoscaling
Forecasting
Load shedding
```

## Pattern B: Bad Deployment

Evidence:

```text
CPU rises after rollout
Only new version is affected
Request rate is unchanged
Hot function appears in profiler
```

Mitigation:

```text
Rollback
Disable feature flag
Reduce traffic to new version
```

## Pattern C: Retry Storm

Evidence:

```text
Dependency errors
Request attempts exceed customer traffic
CPU and network rise
Repeated timeout/retry logs
```

Mitigation:

```text
Circuit breaker
Disable/reduce retries
Backoff with jitter
Rate limit
```

## Pattern D: Garbage Collection

Evidence:

```text
CPU spikes periodically
Pause time rises
Heap near limit
GC logs show frequent collections
```

Mitigation:

```text
Reduce load
Increase memory temporarily
Restart only as controlled mitigation
```

Permanent fix:

```text
Memory leak analysis
Heap tuning
Allocation reduction
GC configuration
```

## Pattern E: High System CPU

Evidence:

```text
%sy is high
Context switches high
Network packet rate high
System calls frequent
```

Possible causes:

```text
Networking
Logging
Lock contention
Many small I/O operations
Container/runtime overhead
```

## Pattern F: High Steal Time

Evidence:

```text
%st is high
VM performance degrades
Application demand is unchanged
```

Meaning:

> The hypervisor is not giving the VM its expected CPU time.

Actions:

```text
Check cloud host/instance metrics
Move or resize instance
Escalate to cloud provider
```

---

# 17. Safe Mitigation

Choose based on evidence:

```text
Scale application
Scale node/VM
Rollback deployment
Disable expensive feature
Throttle non-critical traffic
Stop runaway batch job
Renice low-priority process
Restart service as temporary mitigation
Fail over
```

## Signals Before Killing A Process

Capture:

```bash
ps -fp <pid>
top -H -p <pid>
pidstat -p <pid> 1
lsof -p <pid> | head
```

Graceful termination:

```bash
kill -TERM <pid>
```

Force only if necessary:

```bash
kill -KILL <pid>
```

> [!CAUTION]
> `SIGKILL` gives the process no opportunity to flush data, release locks, or shut down cleanly.

---

# 18. Recovery Validation

After mitigation:

```text
CPU returns to baseline
Run queue falls
p95/p99 latency recovers
Error rate recovers
Queue backlog drains
Health checks pass
Customer transaction succeeds
No dependent system is overloaded
```

Commands:

```bash
uptime
vmstat 1
mpstat -P ALL 1
docker stats --no-stream
```

Business validation:

```bash
./scripts/smoke-test.sh
```

---

# 19. Monitoring And Alerts

VPS CPU:

```promql
100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[2m])) * 100)
```

CPU alert:

```promql
100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[2m])) * 100) > 80
```

Use a pending period:

```text
Warning: above 80% for 5 minutes
Critical: above 90% for 10 minutes with latency/error impact
```

Do not page only because CPU is high.

Better alert:

```text
High CPU + high latency/error rate + sustained duration
```

---

# 20. Production Scenario

## Situation

> Reservation API p95 latency increased from below one second to several seconds during peak traffic.

## Investigation

```text
Grafana showed latency and error increase
CPU was elevated but not fully saturated
AppDynamics showed database connection wait
CloudWatch showed DB connections at ceiling
Splunk showed connection-pool timeout exceptions
```

## Conclusion

> CPU was not the root cause. Connection-pool saturation caused request waiting, retries, and additional CPU overhead.

## Lesson

> Do not stop at the first abnormal metric. Correlate system, application, dependency, and business signals.

---

# 21. Interview-Ready Explanation

> When I troubleshoot high CPU, I first confirm customer impact and determine whether CPU is the actual constraint. I check `uptime` for load trend, `vmstat` for runnable and blocked tasks, `mpstat` for CPU modes and per-core imbalance, and `pidstat` or `top` to identify processes and threads.
>
> I specifically distinguish user CPU, system CPU, I/O wait, and steal time because each leads to a different investigation. I also correlate CPU with memory pressure, disk latency, request rate, errors, p95/p99 latency, container throttling, and recent deployments.
>
> For mitigation, I might scale, roll back, stop a runaway job, throttle non-critical traffic, or restart a service, depending on evidence. Afterward, I validate both infrastructure recovery and the complete customer transaction. The permanent fix may involve capacity planning, code optimization, autoscaling, retry controls, or better resource limits.

---

# 22. Hands-On Lab

Baseline:

```bash
uptime
nproc
vmstat 1
docker stats --no-stream
```

Start controlled CPU load:

```bash
./scripts/demo-cpu-load.sh start
```

Observe:

```bash
uptime
top
vmstat 1
mpstat -P ALL 1
pidstat 1
docker stats --no-stream
```

Check Grafana:

```text
VPS CPU Usage
Load Average
Container CPU
```

Stop:

```bash
./scripts/demo-cpu-load.sh stop
```

Validate:

```bash
./scripts/vps-health-check.sh
./scripts/smoke-test.sh
```

Write a short incident note:

```text
Symptom
Evidence
Mitigation
Recovery validation
Root cause
Preventive action
```

