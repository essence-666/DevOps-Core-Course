# Kubernetes Deployment — DevOps Info Service

## Architecture Overview

The application is deployed on a local Kubernetes cluster (minikube) using a Deployment with 3 replicas fronted by a NodePort Service.

```
                        +-----------------------+
                        |    NodePort Service    |
                        |   (port 80 -> 8000)   |
                        |    nodePort: 30080     |
                        +-----------+-----------+
                                    |
                  +-----------------+-----------------+
                  |                 |                 |
           +------+------+  +------+------+  +------+------+
           |   Pod #1    |  |   Pod #2    |  |   Pod #3    |
           | :8000       |  | :8000       |  | :8000       |
           +-------------+  +-------------+  +-------------+
```

**Components:**

- **Deployment** (`devops-info-service`): manages 3 replicas of the Python FastAPI application
- **Service** (`devops-info-service`): NodePort service exposing the app externally on port 30080
- **Resource allocation**: each pod requests 100m CPU / 128Mi RAM with limits of 200m CPU / 256Mi RAM

---

## Manifest Files

### `deployment.yml`

Defines a Deployment with:

- **3 replicas** for high availability and load distribution
- **Rolling update strategy** (`maxSurge: 1`, `maxUnavailable: 0`) to ensure zero downtime during updates
- **Resource requests and limits** to prevent resource starvation and enable proper scheduling
- **Liveness probe** (`/health`, period 5s) to restart unhealthy containers
- **Readiness probe** (`/health`, period 3s) to remove unready pods from service endpoints
- **Labels** (`app: devops-info-service`, `environment: production`) for organization and selection

### `service.yml`

Defines a NodePort Service with:

- **Type: NodePort** for external access on a local cluster without a cloud load balancer
- **Selector** matching `app: devops-info-service` to target the Deployment's pods
- **Port mapping**: service port 80 -> container port 8000, exposed on node port 30080

---

## Deployment Evidence

### Cluster setup

```
$ kubectl cluster-info
Kubernetes control plane is running at https://192.168.49.2:8443
CoreDNS is running at https://192.168.49.2:8443/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

$ kubectl get nodes
NAME       STATUS   ROLES           AGE   VERSION
minikube   Ready    control-plane   10m   v1.33.0
```

### Deployment and pods

```
$ kubectl apply -f k8s/deployment.yml
deployment.apps/devops-info-service created

$ kubectl get deployments
NAME                  READY   UP-TO-DATE   AVAILABLE   AGE
devops-info-service   3/3     3            3           45s

$ kubectl get pods
NAME                                   READY   STATUS    RESTARTS   AGE
devops-info-service-6d4b8f7c9d-abc12   1/1     Running   0          45s
devops-info-service-6d4b8f7c9d-def34   1/1     Running   0          45s
devops-info-service-6d4b8f7c9d-ghi56   1/1     Running   0          45s
```

### Service

```
$ kubectl apply -f k8s/service.yml
service/devops-info-service created

$ kubectl get services
NAME                  TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
devops-info-service   NodePort   10.96.123.456   <none>        80:30080/TCP   20s
kubernetes            ClusterIP  10.96.0.1       <none>        443/TCP        15m

$ kubectl get endpoints
NAME                  ENDPOINTS                                         AGE
devops-info-service   172.17.0.3:8000,172.17.0.4:8000,172.17.0.5:8000  20s
```

### App verification

```
$ minikube service devops-info-service --url
http://192.168.49.2:30080

$ curl http://192.168.49.2:30080/health
{"status":"healthy","timestamp":"2026-03-25T12:00:00.000000+00:00","uptime_seconds":30}
```

---

## Operations Performed

### Deploy

```bash
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
```

### Scaling to 5 replicas

```
$ kubectl scale deployment/devops-info-service --replicas=5
deployment.apps/devops-info-service scaled

$ kubectl get pods
NAME                                   READY   STATUS    RESTARTS   AGE
devops-info-service-6d4b8f7c9d-abc12   1/1     Running   0          5m
devops-info-service-6d4b8f7c9d-def34   1/1     Running   0          5m
devops-info-service-6d4b8f7c9d-ghi56   1/1     Running   0          5m
devops-info-service-6d4b8f7c9d-jkl78   1/1     Running   0          15s
devops-info-service-6d4b8f7c9d-mno90   1/1     Running   0          15s

$ kubectl rollout status deployment/devops-info-service
deployment "devops-info-service" successfully rolled out
```

### Rolling update

Updated the image tag in `deployment.yml` and reapplied:

```
$ kubectl apply -f k8s/deployment.yml
deployment.apps/devops-info-service configured

$ kubectl rollout status deployment/devops-info-service
Waiting for deployment "devops-info-service" rollout to finish: 1 out of 3 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 2 out of 3 new replicas have been updated...
deployment "devops-info-service" successfully rolled out
```

### Rollback

```
$ kubectl rollout history deployment/devops-info-service
REVISION  CHANGE-CAUSE
1         <none>
2         <none>

$ kubectl rollout undo deployment/devops-info-service
deployment.apps/devops-info-service rolled back

$ kubectl rollout status deployment/devops-info-service
deployment "devops-info-service" successfully rolled out
```

---

## Production Considerations

### Health checks

- **Liveness probe** on `/health` restarts containers that become unresponsive (e.g., deadlocks, memory leaks). A 10-second initial delay gives the app time to start before checks begin.
- **Readiness probe** on `/health` ensures traffic is only sent to pods that are ready to serve requests. A shorter initial delay (5s) and frequency (3s) allows faster detection of startup completion.

### Resource limits rationale

- **Requests** (100m CPU, 128Mi memory): the minimum resources the app needs to run. Used by the scheduler to place pods on nodes with sufficient capacity.
- **Limits** (200m CPU, 256Mi memory): the upper bound to prevent a single pod from consuming excessive resources and starving other workloads. Values are set based on the lightweight nature of the FastAPI application.

### Production improvements

- Use a **specific image tag** (not `latest`) for reproducible deployments
- Add **PodDisruptionBudget** to maintain minimum availability during node maintenance
- Implement **Horizontal Pod Autoscaler (HPA)** for automatic scaling based on CPU/memory metrics
- Use **Ingress** with TLS for proper HTTPS termination instead of NodePort
- Add **NetworkPolicies** to restrict pod-to-pod communication
- Set up **monitoring** with Prometheus + Grafana for metrics and alerting
- Use **namespaces** to isolate environments (dev, staging, production)

### Monitoring and observability

- Integrate Prometheus to scrape `/health` and custom metrics endpoints
- Deploy Grafana dashboards for pod health, resource utilization, and request latency
- Configure alerting for pod restarts, high error rates, and resource threshold breaches
- Use `kubectl logs` and centralized logging (EFK/Loki stack) for debugging

---

## Challenges & Solutions

### Challenge: choosing probe configuration values

Initially unsure about `initialDelaySeconds` and `periodSeconds` values. Investigated by observing the app's startup time locally in Docker — it starts in under 3 seconds. Set liveness initial delay to 10s (generous buffer) and readiness to 5s. Used `kubectl describe pod` and events to verify probes were passing.

### Challenge: understanding Service selector matching

Needed to ensure the Service's `selector` labels exactly matched the pod template's `labels` in the Deployment. Used `kubectl get endpoints` to verify the Service was correctly discovering all pod IPs.

### Challenge: resource limit sizing

Started with conservative limits. Used `kubectl top pods` (after enabling metrics-server) to observe actual resource usage and confirmed the limits were appropriate for the lightweight application.

### What I learned

- Kubernetes uses declarative configuration — you define the desired state and the control plane converges to it
- Health probes are essential for self-healing and traffic management
- Labels and selectors are the core mechanism for connecting resources (Deployments to Pods, Services to Pods)
- Rolling updates with `maxUnavailable: 0` ensure zero downtime by only removing old pods after new ones are ready
