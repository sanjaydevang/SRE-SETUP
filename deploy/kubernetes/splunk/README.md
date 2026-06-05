# Splunk Log Forwarding

This folder contains an optional Fluent Bit DaemonSet for forwarding Kubernetes container logs to Splunk HEC.

The app already writes structured JSON logs to stdout. In Kubernetes, that is the correct application behavior. A node-level agent such as Fluent Bit, Fluentd, or Splunk Connect for Kubernetes collects those logs and forwards them.

## Before Applying

Edit `00-fluent-bit-splunk.yaml`:

- replace `splunk.example.com` with your Splunk HEC host
- replace `replace-with-your-token` with your HEC token
- choose the correct index, for example `crs_lab`

## Apply

```bash
kubectl apply -f deploy/kubernetes/splunk
```

## Useful Splunk Searches

```spl
index=crs_lab service=reservation-service event=reservation_created
```

```spl
index=crs_lab service=notification-worker event=pms_delivery_failed
| stats count by error
```

```spl
index=crs_lab property_id=DAL-100
| table _time service event confirmation_id property_id hotel_tier error
```

## Interview Explanation

> Application containers write structured JSON logs to stdout. In Kubernetes, node-level log agents collect `/var/log/containers/*.log`, enrich records with pod metadata, and forward them to Splunk. During incidents, I search by confirmation ID, property ID, hotel chain, service, event, and error message to trace a booking across the reservation service and PMS notification worker.

