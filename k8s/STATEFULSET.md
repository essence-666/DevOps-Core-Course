# StatefulSets & Persistent Storage

## 1. StatefulSet Overview

### Why StatefulSet?

A `Deployment` treats all pods as interchangeable: any pod can be replaced by any other, storage is either ephemeral or shared via a single PVC, and pod names change on restart. This is ideal for stateless web apps.

A `StatefulSet` provides three guarantees that stateless controllers cannot:

1. **Stable network identity** — pod names are deterministic (`app-0`, `app-1`, `app-2`) and DNS records persist across restarts
2. **Per-pod persistent storage** — `volumeClaimTemplates` create one PVC per pod; `app-0` always mounts `data-app-0`, never another pod's data
3. **Ordered lifecycle** — pods start in order `0 → 1 → 2` and scale down in reverse `2 → 1 → 0`

### Deployment vs StatefulSet

| Feature | Deployment | StatefulSet |
|---------|-----------|-------------|
| Pod names | Random suffix (`app-7d4b9c-xkv2f`) | Ordered index (`app-0`, `app-1`) |
| Pod DNS | Random | Stable: `app-0.app-headless.ns.svc.cluster.local` |
| Storage | Shared PVC (all pods same data) | Per-pod PVC via `volumeClaimTemplates` |
| Scale-up order | Parallel (any order) | Sequential: `0 → 1 → 2` |
| Scale-down order | Parallel (any order) | Reverse: `2 → 1 → 0` |
| Update order | Parallel / rolling | Reverse sequential: `2 → 1 → 0` |
| PVC lifecycle | Deleted with Deployment | Retained when StatefulSet is deleted |

### Stateful Workload Examples

- **Databases**: MySQL, PostgreSQL, MongoDB — each replica needs its own data directory
- **Message queues**: Kafka, RabbitMQ — brokers have unique IDs and topic partitions
- **Distributed systems**: Elasticsearch, Cassandra, ZooKeeper — nodes join clusters by stable name

### Headless Services

A regular `Service` has a `clusterIP` that load-balances across pod endpoints. A **headless service** (`clusterIP: None`) skips the virtual IP and instead creates individual DNS A-records for each pod:

```
<pod-name>.<service-name>.<namespace>.svc.cluster.local
```

For example, with a StatefulSet named `app-python-app-python` and headless service `app-python-app-python-headless`:

```
app-python-app-python-0.app-python-app-python-headless.default.svc.cluster.local
app-python-app-python-1.app-python-app-python-headless.default.svc.cluster.local
app-python-app-python-2.app-python-app-python-headless.default.svc.cluster.local
```

This allows peers to discover and connect to specific instances, which is required for leader election and cluster formation in distributed systems.

---

## 2. Resource Verification

### Deploy StatefulSet

```bash
helm upgrade --install app-python ./k8s/app-python -f k8s/app-python/values-statefulset.yaml
```

### Verify Resources

```bash
kubectl get po,sts,svc,pvc
```

**Expected output:**

```
NAME                           READY   STATUS    RESTARTS   AGE
pod/app-python-app-python-0    1/1     Running   0          2m
pod/app-python-app-python-1    1/1     Running   0          90s
pod/app-python-app-python-2    1/1     Running   0          60s

NAME                                          READY   AGE
statefulset.apps/app-python-app-python        3/3     2m

NAME                                           TYPE        CLUSTER-IP     PORT(S)        AGE
service/app-python-app-python                  NodePort    10.96.45.12    80:30080/TCP   2m
service/app-python-app-python-headless         ClusterIP   None           80/TCP         2m

NAME                                                    STATUS   VOLUME   CAPACITY   ACCESS MODES   AGE
persistentvolumeclaim/data-app-python-app-python-0      Bound    pvc-...  100Mi      RWO            2m
persistentvolumeclaim/data-app-python-app-python-1      Bound    pvc-...  100Mi      RWO            90s
persistentvolumeclaim/data-app-python-app-python-2      Bound    pvc-...  100Mi      RWO            60s
```

Key observations:
- Pods have ordinal suffixes (`-0`, `-1`, `-2`), not random hashes
- Each pod has its own PVC (`data-<name>-<ordinal>`) created by `volumeClaimTemplates`
- Two services: NodePort for external access, headless for DNS identity

---

## 3. Network Identity — DNS Resolution

### Test DNS from Inside a Pod

```bash
kubectl exec -it app-python-app-python-0 -- /bin/sh

# Resolve sibling pod by stable DNS name
nslookup app-python-app-python-1.app-python-app-python-headless
```

**Expected output:**

```
Server:         10.96.0.10
Address:        10.96.0.10#53

Name:   app-python-app-python-1.app-python-app-python-headless.default.svc.cluster.local
Address: 10.244.1.7
```

Compare this to a Deployment: pods resolve via the shared ClusterIP, not directly to individual pod IPs. With a StatefulSet and headless service, each pod has a stable, resolvable DNS name that survives pod restarts (the IP may change, but the hostname stays the same).

### DNS Naming <headless-Pattern

```
<pod-name>.service-name>.<namespace>.svc.cluster.local
    │              │                   │
    │              │                   └── always "svc.cluster.local"
    │              └────────────────────── service name (headless)
    └───────────────────────────────────── statefulset name + ordinal
```

---

## 4. Per-Pod Storage Evidence

Each pod maintains an independent visit counter in its own `/data/visits` file, backed by a separate PVC.

### Test Isolation

```bash
# Forward each pod to a different local port
kubectl port-forward pod/app-python-app-python-0 8080:8000 &
kubectl port-forward pod/app-python-app-python-1 8081:8000 &
kubectl port-forward pod/app-python-app-python-2 8082:8000 &

# Generate visits on pod-0 only
curl localhost:8080/visits
curl localhost:8080/visits
curl localhost:8080/visits

# Check visit counts — only pod-0 should have incremented
curl localhost:8080/visits  # → {"visits": 3}
curl localhost:8081/visits  # → {"visits": 0}
curl localhost:8082/visits  # → {"visits": 0}
```

**Expected result:** Each pod tracks its own counter independently. With a shared PVC (Deployment), all pods would read/write the same counter — leading to race conditions and mixed state. With per-pod PVCs (StatefulSet), storage is fully isolated.

### Verify PVC Binding

```bash
kubectl exec app-python-app-python-0 -- cat /data/visits  # → 3
kubectl exec app-python-app-python-1 -- cat /data/visits  # → 0
kubectl exec app-python-app-python-2 -- cat /data/visits  # → 0
```

---

## 5. Persistence Test — Data Survives Pod Deletion

StatefulSets preserve PVCs when pods are deleted. The replacement pod automatically remounts the same PVC.

```bash
# Record current visit count on pod-0
kubectl exec app-python-app-python-0 -- cat /data/visits
# Output: 3

# Delete the pod (StatefulSet controller will recreate it)
kubectl delete pod app-python-app-python-0

# Watch the pod restart — same ordinal, same PVC
kubectl get pod app-python-app-python-0 -w

# After pod is Running again, verify data is intact
kubectl exec app-python-app-python-0 -- cat /data/visits
# Output: 3  <- same count, data survived
```

This contrasts with:
- **Deployment + emptyDir**: data lost on pod restart
- **Deployment + shared PVC**: data shared and potentially corrupted under concurrent writes
- **StatefulSet + volumeClaimTemplates**: data isolated per pod AND persistent across restarts

**Important:** PVCs created by `volumeClaimTemplates` are **not deleted** when the StatefulSet is deleted. They must be deleted manually to free storage. This is intentional — it protects against accidental data loss.

---

## 6. Bonus — Update Strategies

StatefulSets support two update strategies, configurable via `statefulset.updateStrategy` in `values.yaml`.

### RollingUpdate (default)

Replaces pods in reverse ordinal order (`2 → 1 → 0`), waiting for each to become `Ready` before proceeding.

```yaml
statefulset:
  updateStrategy:
    type: RollingUpdate
    partition: 0  # Update all pods (partition=0 means ordinal >= 0)
```

### Partitioned Rolling Update (Canary for StatefulSets)

When `partition > 0`, only pods with ordinal **>= partition** are updated. Pods below the partition keep the old version. This allows safely testing a new version on a subset of pods before rolling it out fully.

```bash
# Update only pod-2 (ordinal 2 >= partition 2)
helm upgrade app-python ./k8s/app-python \
  -f k8s/app-python/values-statefulset.yaml \
  --set statefulset.updateStrategy.partition=2 \
  --set image.tag=v2

# pod-2 -> new version, pod-0 and pod-1 -> still old version
kubectl get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[0].image}{"\n"}{end}'
```

**Use case:** Staged rollout for databases — verify schema compatibility on replica before updating primary.

### OnDelete Strategy

Pods are **never updated automatically**. A pod only picks up the new template when it is manually deleted. This gives full control over the update timing.

```bash
# Switch to OnDelete strategy
helm upgrade app-python ./k8s/app-python \
  -f k8s/app-python/values-statefulset.yaml \
  --set statefulset.updateStrategy.type=OnDelete \
  --set image.tag=v2

# Pods still run the old image — update is pending
kubectl get pods  # all still showing old image

# Manually trigger update on pod-2
kubectl delete pod app-python-app-python-2
# pod-2 restarts with new image

# Update pod-1 later when ready
kubectl delete pod app-python-app-python-1
```

**Use case:** Applications where the operator must manually verify each replica upgrade — e.g., Kafka broker restarts require topic leader re-election to complete before moving to the next broker.

### Strategy Comparison

| Strategy | Trigger | Order | Use Case |
|----------|---------|-------|----------|
| `RollingUpdate` (partition=0) | Automatic | `2->1->0` | Standard updates |
| `RollingUpdate` (partition=N) | Auto for ordinal >= N | `max->N` | Canary on subset |
| `OnDelete` | Manual pod deletion | Operator-controlled | Critical stateful apps |

---

## CLI Quick Reference

```bash
# Deploy in StatefulSet mode
helm upgrade --install app-python ./k8s/app-python -f k8s/app-python/values-statefulset.yaml

# Watch pod startup (ordered)
kubectl get pods -w

# View StatefulSet details
kubectl describe statefulset app-python-app-python

# List per-pod PVCs
kubectl get pvc -l app.kubernetes.io/instance=app-python

# Exec into specific pod
kubectl exec -it app-python-app-python-0 -- /bin/sh

# Forward specific pod for testing
kubectl port-forward pod/app-python-app-python-0 8080:8000

# Scale StatefulSet
kubectl scale statefulset app-python-app-python --replicas=5

# Trigger partitioned update
helm upgrade app-python ./k8s/app-python \
  -f k8s/app-python/values-statefulset.yaml \
  --set statefulset.updateStrategy.partition=2 \
  --set image.tag=v2
```
