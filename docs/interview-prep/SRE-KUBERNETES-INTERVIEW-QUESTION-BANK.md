# SRE Kubernetes Interview Question Bank

This document turns common SRE/Kubernetes interview questions into answer frameworks. The goal is not memorization. The goal is to build a repeatable troubleshooting mindset:

```text
Symptom -> Scope -> Recent changes -> System layer -> Evidence -> Mitigation -> Root cause -> Prevention
```

Use this with the CRS SRE lab. Later, we will convert these into polished interview stories.

## 1. Pod Pending Troubleshooting

### Question

How would you troubleshoot a pod that is stuck in `Pending` state?

### Strong Answer

I would start by describing the pod and reading the events, because `Pending` usually means the scheduler cannot place the pod on a node.

Commands:

```bash
kubectl get pod -n <namespace>
kubectl describe pod -n <namespace> <pod-name>
kubectl get events -n <namespace> --sort-by=.lastTimestamp
kubectl get nodes
kubectl describe nodes
```

I would check:

- insufficient CPU or memory
- node selector mismatch
- affinity or anti-affinity rules
- taints not tolerated by the pod
- PVC not bound
- image pull issues if it moves beyond scheduling
- quota or limit range restrictions
- topology spread constraints
- GPU or special resource unavailable

### What To Look For In Events

Common events:

```text
0/5 nodes are available: insufficient cpu
0/5 nodes are available: insufficient memory
0/5 nodes are available: node(s) had untolerated taint
0/5 nodes are available: node(s) didn't match node selector
0/5 nodes are available: pod has unbound immediate PersistentVolumeClaims
preemption: no preemption victims found
```

### Interview Line

> A Pending pod is usually a scheduling problem. I first check pod events because they tell me exactly why the scheduler rejected nodes. Then I check node capacity, taints, tolerations, selectors, affinity, PVCs, quotas, and autoscaler behavior.

## 2. Taints And Tolerations

### Question

What are tolerations and what events would you expect to see?

### Strong Answer

Taints are applied to nodes. They repel pods. Tolerations are applied to pods. They allow pods to be scheduled onto tainted nodes.

Example taint:

```bash
kubectl taint nodes node1 dedicated=gpu:NoSchedule
```

Example toleration:

```yaml
tolerations:
  - key: dedicated
    operator: Equal
    value: gpu
    effect: NoSchedule
```

If a pod does not tolerate the taint, events may show:

```text
node(s) had untolerated taint {dedicated: gpu}
```

Effects:

- `NoSchedule`: new pods cannot schedule unless tolerated
- `PreferNoSchedule`: scheduler tries to avoid node
- `NoExecute`: existing pods may be evicted unless tolerated

### Interview Line

> Taints protect nodes. Tolerations allow specific pods to use those nodes. For example, I would taint GPU nodes so only GPU workloads with the correct toleration can run there.

## 3. Cluster Autoscaler Not Adding Nodes

### Question

How would you investigate a cluster autoscaler that is not adding nodes despite resource shortage?

### Strong Answer

First I confirm pods are pending because of resource shortage. Then I inspect autoscaler logs and node group configuration.

Commands:

```bash
kubectl get pods -A | grep Pending
kubectl describe pod -n <namespace> <pod>
kubectl logs -n kube-system deployment/cluster-autoscaler
kubectl get nodes
```

I would check:

- pending pod events show insufficient CPU/memory
- node group reached max size
- autoscaler does not manage that node group
- cloud provider quota limit reached
- requested instance type unavailable
- pod has node selector or affinity that no scalable node group matches
- pod requests GPU but no GPU node group exists
- pod uses local storage or constraints that block scale-up
- cluster autoscaler lacks IAM/cloud permissions
- autoscaler is in backoff after failed scale-up

### Interview Line

> Autoscaler only adds nodes if pending pods are schedulable on a node group it controls. If constraints, quotas, max node count, taints, or permissions prevent scale-up, pods remain pending even when the cluster looks busy.

## 4. Multiple Nodes Unavailable

### Question

If multiple nodes become unavailable simultaneously, what are possible causes?

### Strong Answer

I would treat this as a potential infrastructure or control-plane incident and scope quickly.

Possible causes:

- cloud provider AZ outage
- network partition
- CNI failure
- node OS/kernel issue
- bad DaemonSet rollout
- kubelet crash
- container runtime failure
- disk pressure across nodes
- autoscaler or node group replacement
- expired certificates
- security group or firewall change
- underlying hypervisor/VM issue

Commands:

```bash
kubectl get nodes -o wide
kubectl describe node <node>
kubectl get events -A --sort-by=.lastTimestamp
kubectl get pods -A -o wide
```

### Interview Line

> If several nodes fail together, I look for shared failure domains: same AZ, same node group, same CNI, same DaemonSet, same OS image, or same cloud provider event.

## 5. Load Balancer Receives Traffic But Backend Does Not

### Question

What is the first step when traffic reaches the load balancer but does not reach backend servers?

### Strong Answer

I would check whether the load balancer has healthy backend targets. If targets are unhealthy, I inspect health checks and backend connectivity.

Checks:

- LB target health
- service endpoints
- pod readiness
- security groups/firewall
- ingress rules
- service selector
- port mismatch
- backend app health endpoint

Kubernetes commands:

```bash
kubectl get svc -n <namespace>
kubectl get endpoints -n <namespace> <service-name>
kubectl describe ingress -n <namespace>
kubectl describe pod -n <namespace> <pod>
```

### Interview Line

> If the load balancer receives traffic but backends do not, I first check target health and service endpoints. In Kubernetes, a common cause is pods not being Ready, so the Service has no endpoints.

## 6. Terraform Apply Failed Midway

### Question

How do you recover from a Terraform apply that fails midway?

### Strong Answer

I do not immediately rerun blindly. First I inspect what was created, compare it with Terraform state, and run a new plan.

Steps:

```bash
terraform state list
terraform plan
terraform show
```

Then:

- identify resources created before failure
- identify resources missing from state
- check provider/cloud console
- fix the root issue
- import orphaned resources if needed
- remove bad state only if confirmed
- rerun `terraform plan`
- apply after plan is clean

Useful commands:

```bash
terraform import <resource> <id>
terraform state rm <resource>
terraform refresh
terraform plan
```

### Interview Line

> Terraform is state-driven, so after a failed apply I reconcile real infrastructure with state before rerunning. The goal is to avoid duplicate resources or drift.

## 7. Alert Fatigue

### Question

How would you identify alert fatigue when critical alerts fire continuously?

### Strong Answer

I would analyze alert history and compare alerts to real incidents.

I would check:

- number of alerts per week/month
- duplicate alerts from same root cause
- alerts firing without action taken
- alerts acknowledged but ignored
- alerts firing outside user impact
- severity mismatch
- noisy static thresholds
- lack of grouping or inhibition

Evidence:

- PagerDuty alert volume
- Grafana alert history
- incident tickets
- postmortems
- on-call feedback

### Interview Line

> Alert fatigue happens when alerts are not actionable or not tied to user impact. I tune alerts using incident history, SLOs, burn rates, grouping, inhibition, and better severity classification.

## 8. Reduce False Positives

### Question

How would you reduce false positives in alerts?

### Strong Answer

I would replace noisy absolute thresholds with user-impact or SLO-based alerts where possible.

Techniques:

- use rate or increase instead of raw counters
- add pending period
- use multi-window burn-rate alerts
- group related alerts
- inhibit lower-priority alerts when a higher-level alert fires
- alert on symptoms before causes
- tune thresholds using historical baseline
- route warning alerts to Slack and critical alerts to PagerDuty

Example:

Bad:

```promql
crs_dlq_messages_total > 0
```

Better:

```promql
sum(increase(crs_dlq_messages_total[5m])) > 0
```

### Interview Line

> I reduce false positives by making alerts actionable, time-windowed, and tied to user impact. I also review alert history against actual incidents.

## 9. Monitoring Shows Healthy But Users Report Failures

### Question

How would you investigate an incident where monitoring shows healthy but users report failures?

### Strong Answer

I would assume monitoring has a blind spot.

I would check:

- synthetic tests from user locations
- logs for affected user IDs or request IDs
- load balancer access logs
- DNS/CDN issues
- external dependency failures
- specific geography, partner, or device
- partial endpoint failure not covered by dashboards
- business transaction success, not just infrastructure health

For CRS:

- API may be healthy
- PMS delivery may fail silently
- specific hotel chain may be affected
- HTTP 200 may hide business failure

### Interview Line

> Healthy infrastructure does not always mean healthy user experience. I verify the full business transaction path and look for monitoring gaps.

## 10. Complex Production Issue Methodology

### Question

Walk me through the most complex production issue you resolved.

### Answer Framework

Use this structure:

1. Business impact
2. Alert or user report
3. Initial scope
4. Evidence gathered
5. Hypotheses ruled out
6. Root cause
7. Mitigation
8. Permanent fix
9. Prevention
10. Result

### CRS Story Example

> We had a reservation error spike affecting all OTA partners. I scoped whether it was one partner or system-wide, then checked Grafana error rate, AppDynamics traces, CloudWatch DB connections, and Splunk logs. Traces showed requests stalling before query execution while waiting for DB connections. CloudWatch showed the connection pool was maxed out, and Splunk showed thousands of connection timeout exceptions. Root cause was a bad deploy setting connection timeout incorrectly. We mitigated by increasing pool size and restarting pods, then the dev team reverted the config. Preventive actions included a DB pool utilization alert, post-deploy checklist update, and CI guardrail for invalid timeout config.

## 11. Incident Communication

### Question

What is the first thing you do to communicate during an incident?

### Strong Answer

I acknowledge the incident and create a communication channel quickly.

First actions:

- acknowledge page
- open incident bridge or Slack war room
- post initial status
- assign roles if needed
- start timeline
- communicate known impact and next update time

Initial message:

```text
We are investigating elevated PMS delivery failures for Tier 1 hotel reservations. Current impact is being scoped. Next update in 10 minutes.
```

### Interview Line

> During incidents, silence creates confusion. Even if root cause is unknown, I communicate impact, scope, owner, and next update time.

## 12. Rollback Strategy

### Question

What is your rollback strategy?

### Strong Answer

Rollback depends on the change type.

For app deploy:

```bash
kubectl rollout undo deployment/reservation-service -n crs-lab
```

For config:

- revert ConfigMap or Secret change
- restart affected pods if needed

For database:

- avoid destructive migrations
- use backward-compatible schema changes
- restore only if necessary

For Terraform:

- revert code and apply
- do not manually delete unless state is understood

### Interview Line

> I prefer fast rollback for application issues and forward fixes for data/schema issues. Rollback strategy must be tested before production.

## 13. Deployment Strategies

### Question

What deployment strategy have you used?

### Strong Answer

Common strategies:

- rolling update
- blue-green
- canary
- recreate

Rolling update:

> Replace pods gradually. Good default for stateless services.

Blue-green:

> Maintain two environments and switch traffic. Good for fast rollback.

Canary:

> Send small traffic percentage to new version, monitor, then increase.

For CRS:

> I would use rolling updates for low-risk service changes, blue-green for major release cutovers, and canary for high-risk reservation or PMS delivery logic.

## 14. Important Kubernetes Metrics

### Question

What metrics are most important for troubleshooting Kubernetes workloads?

### Strong Answer

Cluster/node:

- node CPU/memory
- disk pressure
- network errors
- node readiness
- pod capacity

Pod/workload:

- CPU/memory requests vs usage
- restart count
- OOMKilled
- pending pods
- readiness failures
- liveness failures

Application:

- request rate
- error rate
- latency
- queue depth
- DLQ count
- dependency failures

Control plane:

- API server latency
- scheduler pending queue
- etcd health
- controller manager health

### Interview Line

> I combine Kubernetes infrastructure metrics with application-level RED metrics. A pod can be Running but the business transaction can still be failing.

## 15. Configuration Drift

### Question

Do you use strategies to avoid configuration drift?

### Strong Answer

Yes:

- infrastructure as code
- GitOps
- Terraform remote state
- pull requests for infra changes
- policy as code
- drift detection
- avoid manual console changes
- standard modules
- periodic `terraform plan`

### Interview Line

> I avoid drift by making Git the source of truth and using Terraform modules, reviewed pull requests, remote state, and periodic drift checks.

## 16. GitHub Actions Or Jenkins Pipeline For Kubernetes

### Question

Walk me through a pipeline you implemented for Kubernetes deployments.

### Strong Answer

Pipeline flow:

1. developer pushes branch
2. CI runs tests
3. build Docker image
4. scan image
5. push image to registry
6. update Kubernetes manifest or Helm values
7. deploy to dev
8. run smoke tests
9. manual approval
10. deploy to prod
11. watch rollout

Commands:

```bash
kubectl apply -f deploy/kubernetes/base
kubectl rollout status deployment/reservation-service -n crs-lab
```

### Interview Line

> A good pipeline validates code, builds immutable images, deploys declaratively, runs smoke tests, and verifies rollout health before calling the deployment successful.

## 17. Helm

### Question

Explain your experience with Helm.

### Strong Answer

Helm is a package manager for Kubernetes. It templates Kubernetes manifests and lets us manage releases.

Helm concepts:

- Chart
- values.yaml
- templates
- release
- upgrade
- rollback

Commands:

```bash
helm install crs ./chart
helm upgrade crs ./chart -f values-prod.yaml
helm rollback crs 1
helm history crs
```

### Interview Line

> I use Helm to package reusable Kubernetes deployments. Values files let us separate environment-specific config from templates.

## 18. Terraform Modules

### Question

How did you structure reusable Terraform modules?

### Strong Answer

I structure modules by infrastructure capability:

```text
modules/vpc
modules/eks
modules/rds
modules/redis
modules/sqs
modules/observability
environments/dev
environments/stage
environments/prod
```

Each module has:

```text
main.tf
variables.tf
outputs.tf
README.md
```

### Interview Line

> I design Terraform modules around reusable infrastructure patterns. Environment folders pass variables into modules, which keeps production, staging, and development consistent while allowing controlled differences.

## 19. DaemonSet

### Question

Can you run a job on a DaemonSet?

### Strong Answer

A DaemonSet ensures one pod runs on each node. It is not a Job, but you can use it for node-level tasks.

Examples:

- log collectors
- monitoring agents
- CNI plugins
- node cleanup agents

If you need a one-time task on every node, you can run a DaemonSet temporarily, then remove it after completion.

### Interview Line

> A DaemonSet is for node-level continuous or per-node workloads. For one-time execution, I would usually use a Job, but for one-time per-node work, a temporary DaemonSet can be used carefully.

## 20. What Happens If A Node Dies?

### Question

What happens internally if a node dies? Will the pod migrate?

### Strong Answer

Pods do not literally migrate. Kubernetes creates replacement pods elsewhere.

Flow:

1. kubelet stops reporting
2. node becomes `NotReady`
3. node controller marks node unhealthy
4. pods on that node are considered unavailable
5. ReplicaSet/Deployment creates replacement pods on healthy nodes
6. scheduler places new pods
7. services route traffic only to ready endpoints

Important:

- stateless pods can be recreated easily
- stateful pods depend on storage attachment and StatefulSet behavior
- replacement is not instant

### Interview Line

> Kubernetes does not move a running pod. It recreates a replacement pod on a healthy node if the workload controller requires it.

## 21. How Kubernetes Scheduler Decides Pod Placement

### Question

How does Kubernetes decide where to run a pod?

### Strong Answer

The scheduler goes through filtering and scoring.

Filter stage:

- does node have enough CPU/memory?
- does node match selector?
- does pod tolerate node taints?
- does affinity match?
- is volume available?
- does topology constraint allow it?

Score stage:

- prefer balanced resource usage
- prefer affinity
- spread pods
- choose best node

Then it binds the pod to the selected node.

### Interview Line

> The scheduler first filters out impossible nodes, then scores remaining nodes and binds the pod to the best one.

## 22. Scaling Cluster During Traffic Surge

### Question

How would you scale your cluster if it cannot handle a traffic surge?

### Strong Answer

Short-term:

- scale deployments
- increase HPA max replicas
- add nodes or increase node group max
- reduce non-critical workloads
- use priority classes
- enable cluster autoscaler

Commands:

```bash
kubectl scale deployment reservation-service -n crs-lab --replicas=10
kubectl get hpa -A
kubectl top pods -n crs-lab
kubectl top nodes
```

Long-term:

- right-size requests/limits
- improve autoscaling
- cache more
- tune queues
- capacity planning

### Interview Line

> During a surge, I scale both workload replicas and node capacity. Then I verify whether bottleneck is CPU, memory, DB, cache, queue, or external dependency.

## 23. Pod-To-Pod Communication

### Question

Define pod-to-pod communication. How does it work?

### Strong Answer

Every pod gets an IP. Kubernetes networking expects pods to communicate without NAT across nodes.

Flow:

```text
pod -> service DNS -> ClusterIP -> endpoint pod IP
```

Example:

```text
reservation-service calls redis:6379
notification-worker calls mock-pms:9000
```

DNS:

```text
mock-pms.crs-lab.svc.cluster.local
```

### Interview Line

> Pods communicate through the Kubernetes network. Usually services provide stable DNS names and load balancing to pod endpoints.

## 24. CNI

### Question

Have you used any CNI? Give an example.

### Strong Answer

CNI means Container Network Interface. It provides pod networking.

Examples:

- Calico
- Cilium
- Flannel
- AWS VPC CNI
- Azure CNI

### Interview Line

> CNI plugins assign pod IPs and implement network connectivity. Some CNIs like Calico and Cilium also support network policy enforcement.

## 25. Network Policies

### Question

Explain network policies. How can we strengthen them?

### Strong Answer

NetworkPolicies control which pods can talk to which pods.

Default Kubernetes allows broad pod communication unless restricted.

Strengthening:

- default deny ingress
- default deny egress
- allow only required service-to-service traffic
- restrict namespace communication
- restrict database access
- use labels carefully
- test policy impact

Example:

> Only `reservation-service` should talk to Postgres. Only `notification-worker` should talk to Mock PMS.

### Interview Line

> Network policies reduce lateral movement by allowing only required pod-to-pod traffic.

## 26. Are You Responsible For Which Pod Lands On Which Node?

### Strong Answer

Usually no, the scheduler handles placement. But SREs influence scheduling using:

- resource requests
- taints and tolerations
- node selectors
- node affinity
- pod anti-affinity
- topology spread constraints
- priority classes

### Interview Line

> I do not manually place pods in normal operations. I define constraints and let the scheduler make placement decisions.

## 27. Five Minutes To Fix Scheduling Issue

### Question

If you have only five minutes to fix a scheduling or placement issue, what would you do?

### Strong Answer

I would inspect events and remove the immediate blocker.

Commands:

```bash
kubectl describe pod -n <ns> <pod>
kubectl get nodes
kubectl describe nodes
```

Fast mitigations:

- reduce pod resource requests temporarily
- scale down non-critical workloads
- add toleration if appropriate
- remove wrong node selector
- increase node group capacity
- manually scale node group

### Interview Line

> In five minutes, I focus on pod events. The events usually tell me whether the issue is resources, taints, selectors, affinity, or PVCs.

## 28. 150 Runner Pipelines On One Node Causing OOM

### Question

With 150 runner pipelines on one node causing OOM, fastest solution?

### Strong Answer

Immediate:

- cordon the node
- stop or reduce runner concurrency
- scale runner replicas across nodes
- add node capacity
- set resource requests/limits

Commands:

```bash
kubectl cordon <node>
kubectl scale deployment <runner-deployment> --replicas=<n>
```

Long-term:

- use dedicated runner node pool
- enforce requests/limits
- use pod anti-affinity
- set max concurrent jobs
- autoscale runners

### Interview Line

> Fastest unblock is reduce concurrency and spread runners across more nodes. Long-term, isolate CI runners with dedicated node pools, resource limits, and autoscaling.

## 29. GPU Workloads

### Question

How do you request GPU in YAML?

### Strong Answer

Use vendor resource key:

```yaml
resources:
  limits:
    nvidia.com/gpu: 1
```

Usually GPU is set in limits. Kubernetes treats it as an extended resource.

### Isolate GPU Node

Use taint:

```bash
kubectl taint nodes gpu-node dedicated=gpu:NoSchedule
```

Pod toleration:

```yaml
tolerations:
  - key: dedicated
    operator: Equal
    value: gpu
    effect: NoSchedule
```

Node selector:

```yaml
nodeSelector:
  accelerator: nvidia
```

### Prevent AI Workloads Consuming Entire Cluster

Use:

- namespaces
- ResourceQuota
- LimitRange
- priority classes
- dedicated node pools
- taints/tolerations
- admission policies
- HPA/KEDA limits

### Interview Line

> GPU workloads should run on isolated node pools with taints, tolerations, quotas, and clear priority classes so they do not starve critical services.

## 30. Priority Classes

### Question

Have you used priority classes?

### Strong Answer

PriorityClass lets Kubernetes decide which pods are more important. High-priority pods can preempt lower-priority pods if needed.

Example:

```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: critical-sre-workload
value: 100000
globalDefault: false
description: Critical workload priority.
```

Pod:

```yaml
priorityClassName: critical-sre-workload
```

### Interview Line

> Priority classes help protect critical workloads during resource pressure, but they must be used carefully because preemption can disrupt lower-priority services.

## 31. Node 70 Percent CPU But Pods Pending

### Question

If a node reaches 70% CPU utilization but pods are still pending, how do you investigate?

### Strong Answer

Utilization and allocatable capacity are different.

I would check:

- pod requests, not just actual usage
- node allocatable CPU
- taints/tolerations
- selectors/affinity
- topology spread
- quotas
- other nodes

Commands:

```bash
kubectl describe pod <pod>
kubectl describe node <node>
kubectl top node
kubectl get pods -A -o wide
```

### Interview Line

> Scheduler uses requested resources, not current CPU usage. A node at 70% actual CPU may still have no allocatable requested CPU left.

## 32. Topology Spread Constraints

### Question

Explain topology spread constraints.

### Strong Answer

Topology spread constraints distribute pods across failure domains like nodes, zones, or regions.

Example:

> Spread replicas across availability zones so one AZ failure does not take all replicas down.

Fields:

- `topologyKey`
- `maxSkew`
- `whenUnsatisfiable`
- `labelSelector`

### Interview Line

> Topology spread constraints help avoid placing too many replicas in the same failure domain.

## 33. Deployment With 100 Replicas Had All Pods Deleted

### Question

A deployment with 100 replicas had all pods deleted. What happens internally?

### Strong Answer

If the Deployment and ReplicaSet still exist, Kubernetes recreates pods.

Flow:

1. pods deleted
2. ReplicaSet observes desired replicas are missing
3. ReplicaSet creates new pods
4. scheduler places pods
5. kubelet starts containers
6. readiness gates traffic

Commands:

```bash
kubectl get deploy
kubectl get rs
kubectl get pods -w
kubectl describe deploy <deployment>
```

### Should We Notify Users?

Depends on impact.

Notify if:

- customer traffic was impacted
- SLO breached
- critical functionality unavailable
- recovery time is uncertain

Do not over-notify if:

- no user impact
- pods recovered immediately
- redundancy prevented impact

### Interview Line

> The controller will recreate deleted pods, but as SRE I still check impact, root cause, and whether notification is needed based on user impact and SLA.

## 34. Why Kubernetes Uses etcd

### Question

Why does Kubernetes use etcd instead of PostgreSQL?

### Strong Answer

etcd is a distributed key-value store designed for:

- strongly consistent cluster state
- watch API
- simple key-value data model
- leader election
- low-latency control-plane operations

Kubernetes needs a state store for desired and current cluster state, not relational queries.

### Interview Line

> Kubernetes uses etcd because it needs a strongly consistent distributed key-value store with watch semantics for control-plane state.

## 35. Scheduler Framework

### Question

Describe the Kubernetes scheduler framework stages.

### Strong Answer

High-level stages:

1. QueueSort
2. PreFilter
3. Filter
4. PostFilter
5. PreScore
6. Score
7. Reserve
8. Permit
9. PreBind
10. Bind
11. PostBind

Simple explanation:

> The scheduler picks a pending pod, filters nodes that cannot run it, scores nodes that can run it, reserves the selected node, and binds the pod to that node.

### Interview Line

> The scheduler framework is plugin-based. Different plugins participate in filtering, scoring, binding, and other extension points.

## 36. Service Mesh / Istio

### Question

Have you worked with Istio or service mesh?

### Strong Answer If Limited Experience

> I have not managed a large Istio production environment end to end, but I understand the concepts. A service mesh adds sidecar proxies or ambient data plane to handle service-to-service traffic, mTLS, retries, traffic splitting, observability, and policy. For example, Istio can support canary releases by routing 10% traffic to a new version and 90% to stable.

Concepts:

- Envoy proxy
- mTLS
- VirtualService
- DestinationRule
- traffic splitting
- retries/timeouts
- circuit breaking

## 37. Datadog And Grafana

### Question

Did you build observability pipelines using Grafana and Datadog?

### Strong Answer If Grafana Stronger Than Datadog

> I have hands-on experience building Grafana and Prometheus observability in this lab, and in production-style environments I understand how Datadog would serve a similar role for metrics, logs, traces, dashboards, and monitors. The core observability principles are the same: collect metrics/logs/traces, tag them by service/environment, build dashboards around user journeys, and alert on actionable symptoms.

## 38. How Many Clusters / Nodes Have You Managed?

### Strong Answer Template

Be honest. Do not exaggerate.

Example:

> In my previous production support role, I worked with Kubernetes workloads operationally: checking pods, logs, deployments, and service health during incidents and releases. I was not the sole platform owner for all cluster lifecycle operations. For hands-on growth, I built this CRS lab with Kubernetes manifests, Prometheus, Grafana, and Splunk-ready logging to practice deployment and troubleshooting end to end.

## 39. LLM / Ray / vLLM / KServe

### Question

How would you run an LLM inference workload?

### Strong Answer

I would treat it as a GPU-backed, latency-sensitive workload.

Consider:

- model size
- GPU type
- memory requirement
- inference framework like vLLM, TGI, Triton, or KServe
- autoscaling
- batching
- request timeout
- queueing
- model warmup
- observability
- GPU isolation

### Interview Line

> For LLM inference, I would use dedicated GPU node pools, request GPU resources, isolate workloads with taints/tolerations, monitor GPU utilization and latency, and use an inference framework such as vLLM or KServe depending on platform maturity.

## 40. How To Practice These Questions

For each question, practice this format:

```text
1. What is the symptom?
2. What command do I run first?
3. What evidence am I looking for?
4. What are the likely causes?
5. What is the fastest mitigation?
6. What is the permanent fix?
7. How do I explain it in business terms?
```

Example:

```text
Question: Pod is Pending
First command: kubectl describe pod
Evidence: scheduler events
Causes: CPU, memory, taints, selectors, PVC, quota
Mitigation: add capacity or adjust constraints
Permanent fix: right-size requests, autoscaler, policy
Business impact: service capacity unavailable
```

