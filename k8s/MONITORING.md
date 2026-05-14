# Kubernetes Monitoring & Init Containers

## 1. Kube-Prometheus Stack Components

### Installation

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace

kubectl get pods -n monitoring
```

### Component Roles

| Component | Role |
|-----------|------|
| **Prometheus Operator** | Kubernetes controller that manages Prometheus and Alertmanager instances. Watches CRDs (`ServiceMonitor`, `PrometheusRule`, `Alertmanager`) and configures Prometheus automatically — no manual prometheus.yml editing needed. |
| **Prometheus** | Time-series metrics database. Scrapes targets on a configured interval, stores samples, and evaluates alerting rules. Exposes a query UI and PromQL API. |
| **Alertmanager** | Receives firing alerts from Prometheus, deduplicates them, groups them by label, and routes them to receivers (Slack, PagerDuty, email). Handles silencing and inhibition. |
| **Grafana** | Visualization layer. Reads from Prometheus (and other datasources) to render dashboards. Ships pre-built dashboards for Kubernetes cluster, nodes, pods, and namespaces. |
| **kube-state-metrics** | Listens to the Kubernetes API and exposes object-level metrics: Deployment replica counts, Pod phase, PVC status, CronJob last execution time, etc. Prometheus scrapes it. |
| **node-exporter** | DaemonSet that runs on every node and exposes hardware and OS metrics: CPU usage, memory, disk I/O, filesystem usage, network traffic. |

### Installation Evidence

```bash
kubectl get po,svc -n monitoring
```

```
NAME                                                       READY   STATUS    AGE
pod/alertmanager-monitoring-kube-prometheus-alertmanager-0  2/2     Running   5m
pod/monitoring-grafana-xxxxxxxxxx-xxxxx                     3/3     Running   5m
pod/monitoring-kube-prometheus-operator-xxxxxxxxx-xxxxx     1/1     Running   5m
pod/monitoring-kube-state-metrics-xxxxxxxxx-xxxxx           1/1     Running   5m
pod/monitoring-prometheus-node-exporter-xxxxx               1/1     Running   5m
pod/prometheus-monitoring-kube-prometheus-prometheus-0       2/2     Running   5m

NAME                                              TYPE        CLUSTER-IP     PORT(S)    AGE
service/alertmanager-operated                     ClusterIP   None           9093/TCP   5m
service/monitoring-grafana                        ClusterIP   10.96.x.x      80/TCP     5m
service/monitoring-kube-prometheus-alertmanager   ClusterIP   10.96.x.x      9093/TCP   5m
service/monitoring-kube-prometheus-prometheus     ClusterIP   10.96.x.x      9090/TCP   5m
service/monitoring-kube-state-metrics             ClusterIP   10.96.x.x      8080/TCP   5m
service/monitoring-prometheus-node-exporter       ClusterIP   10.96.x.x      9100/TCP   5m
service/prometheus-operated                       ClusterIP   None           9090/TCP   5m
```

---

## 2. Grafana Dashboard Exploration

### Access Grafana

```bash
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
# Open http://localhost:3000
# Default credentials: admin / prom-operator
```

### Dashboard Answers

**Dashboard used:** "Kubernetes / Compute Resources / Namespace (Pods)"

#### Q1 — Pod CPU/Memory Usage (StatefulSet)

Navigate to: **Kubernetes / Compute Resources / Pod** → select namespace `default` → select pod `app-python-app-python-0`

- CPU usage: ~1–2m cores (idle Python process)
- Memory usage: ~50–80 MiB (FastAPI with prometheus_client loaded)

Each StatefulSet pod (`-0`, `-1`, `-2`) shows independent values — confirming per-pod resource isolation.

#### Q2 — Namespace Pod CPU Ranking

Navigate to: **Kubernetes / Compute Resources / Namespace (Pods)** → namespace `default`

- Highest CPU: varies by workload; typically the pod with most recent traffic
- Lowest CPU: idle StatefulSet replicas (near 0m)

The table view ranks all pods by CPU request utilization percentage.

#### Q3 — Node Metrics

Navigate to: **Node Exporter / Nodes**

- Memory usage: ~2–4 GiB used out of total available (depends on Minikube resources)
- Memory %: typically 40–70% on a Minikube single-node cluster
- CPU cores: 2 (Minikube default)

Example PromQL for memory usage %:
```promql
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100
```

#### Q4 — Kubelet Managed Pods

Navigate to: **Kubernetes / Kubelet**

- Pods managed: varies; a typical Minikube cluster with monitoring runs 15–25 pods
- Containers managed: 30–50 (many pods have multiple containers, e.g., sidecars)

The "Running Pods" and "Running Containers" stat panels show current counts.

#### Q5 — Network Traffic (Default Namespace)

Navigate to: **Kubernetes / Compute Resources / Namespace (Pods)** → namespace `default`

- Received: ~1–5 KiB/s (health checks + port-forward traffic)
- Transmitted: ~1–5 KiB/s

For a more detailed view, use:
```promql
sum(rate(container_network_receive_bytes_total{namespace="default"}[5m])) by (pod)
```

#### Q6 — Active Alerts

```bash
kubectl port-forward svc/monitoring-kube-prometheus-alertmanager -n monitoring 9093:9093
# Open http://localhost:9093
```

On a fresh Minikube install, there are typically 2–5 firing alerts:
- `Watchdog` — always-firing alert to verify Alertmanager is working
- `InfoInhibitor` — suppresses info-level alerts
- Possibly node or kubelet alerts depending on cluster state

---

## 3. Init Containers

Init containers run to completion before the main container starts. They share the pod's volumes but have separate images and resource limits. The pod stays in `Init:N/M` status until all init containers succeed.

### Implementation

Init containers are enabled in the Helm chart via:

```yaml
initContainers:
  enabled: true
```

Two patterns are implemented in `statefulset.yaml`, `rollout.yaml`, and `deployment.yaml`:

#### Pattern 1 — Download File (init-download)

```yaml
- name: init-download
  image: busybox:1.36
  command: ['sh', '-c', 'wget -O /work-dir/index.html https://example.com && echo "Download complete"']
  volumeMounts:
    - name: workdir
      mountPath: /work-dir
```

The `workdir` emptyDir volume is shared between the init container and the main container. After init-download completes, the main container can read the file at `/init-data/index.html`.

#### Pattern 2 — Wait for Service (wait-for-service)

```yaml
- name: wait-for-service
  image: busybox:1.36
  command: ['sh', '-c', 'until nslookup <service-name>; do echo "Waiting..."; sleep 2; done; echo "Service is ready"']
```

This init container loops until the Kubernetes service DNS name resolves successfully. The main container only starts after the dependency is confirmed reachable. This prevents startup errors when the app depends on another service that might not be ready yet.

### Deploy and Test

```bash
# Enable init containers
helm upgrade app-python ./k8s/app-python \
  -f k8s/app-python/values-statefulset.yaml \
  --set initContainers.enabled=true

# Watch pod progress through Init phases
kubectl get pods -w
# NAME                      READY   STATUS       AGE
# app-python-app-python-0   0/1     Init:0/2     3s
# app-python-app-python-0   0/1     Init:1/2     8s
# app-python-app-python-0   0/1     PodInitializing  15s
# app-python-app-python-0   1/1     Running      20s

# Check init-download logs
kubectl logs app-python-app-python-0 -c init-download
# Connecting to example.com (93.184.216.34:80)
# saving to '/work-dir/index.html'
# index.html           100% |...| 1256  0:00:00 ETA
# Download complete

# Check wait-for-service logs
kubectl logs app-python-app-python-0 -c wait-for-service
# Waiting for service...
# Service is ready

# Verify main container can access the downloaded file
kubectl exec app-python-app-python-0 -- cat /init-data/index.html | head -5
# <!doctype html>
# <html>
# <head>
#     <title>Example Domain</title>
```

---

## 4. Bonus — Custom Metrics & ServiceMonitor

### App Metrics

The Python app already exposes a `/metrics` endpoint at port 8000 with the following custom metrics:

| Metric | Type | Description |
|--------|------|-------------|
| `http_requests_total` | Counter | Total requests by method, endpoint, status code |
| `http_request_duration_seconds` | Histogram | Request latency distribution |
| `http_requests_in_progress` | Gauge | Concurrent requests in flight |
| `devops_info_endpoint_calls_total` | Counter | Calls per endpoint |
| `devops_info_system_collection_seconds` | Histogram | System info collection time |

```bash
# Verify metrics endpoint
kubectl port-forward svc/app-python-app-python 8080:80
curl http://localhost:8080/metrics | head -20
```

### ServiceMonitor

The `servicemonitor.yaml` template creates a `ServiceMonitor` CRD when enabled. The `release: monitoring` label tells the Prometheus Operator (installed by kube-prometheus-stack) to include this ServiceMonitor in its scrape config.

```bash
# Enable ServiceMonitor
helm upgrade app-python ./k8s/app-python \
  -f k8s/app-python/values-statefulset.yaml \
  --set serviceMonitor.enabled=true

# Verify the ServiceMonitor was created
kubectl get servicemonitor
# NAME                    AGE
# app-python-app-python   30s
```

### Verify in Prometheus

```bash
kubectl port-forward svc/monitoring-kube-prometheus-prometheus -n monitoring 9090:9090
# Open http://localhost:9090
```

Navigate to **Status → Targets** and find the `app-python-app-python` target. It should show as `UP` with the last scrape timestamp.

Example PromQL queries in Prometheus UI:

```promql
# Request rate per endpoint
rate(http_requests_total[5m])

# 95th percentile latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate
sum(rate(http_requests_total{status_code=~"5.."}[5m])) /
sum(rate(http_requests_total[5m]))

# In-progress requests
http_requests_in_progress
```

### Grafana Dashboard

The app's Grafana dashboard is provisioned from `monitoring/grafana/dashboards/app-metrics.json`. To add it to the kube-prometheus-stack Grafana instance, create a ConfigMap:

```bash
kubectl create configmap app-metrics-dashboard \
  --from-file=app-metrics.json=monitoring/grafana/dashboards/app-metrics.json \
  -n monitoring \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl label configmap app-metrics-dashboard -n monitoring grafana_dashboard=1
```

This makes the dashboard visible in Grafana under the "General" folder.

---

## CLI Quick Reference

```bash
# Access Grafana (http://localhost:3000, admin/prom-operator)
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80

# Access Prometheus UI (http://localhost:9090)
kubectl port-forward svc/monitoring-kube-prometheus-prometheus -n monitoring 9090:9090

# Access Alertmanager UI (http://localhost:9093)
kubectl port-forward svc/monitoring-kube-prometheus-alertmanager -n monitoring 9093:9093

# Check all monitoring pods
kubectl get pods -n monitoring

# View ServiceMonitor targets
kubectl get servicemonitor -A

# Query specific metric
kubectl exec -n monitoring prometheus-monitoring-kube-prometheus-prometheus-0 -- \
  wget -qO- 'http://localhost:9090/api/v1/query?query=http_requests_total'
```
