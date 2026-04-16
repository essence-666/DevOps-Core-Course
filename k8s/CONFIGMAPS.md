# ConfigMaps & Persistent Volumes Documentation

## Overview

This document covers the implementation for Lab 12: application visit-counter persistence, Kubernetes ConfigMaps (file-based and environment-variable-based), PersistentVolumeClaims, and ConfigMap hot-reload via checksum annotations.

---

## Task 1 — Application Persistence Upgrade

### Visit Counter Implementation

Both applications now track the number of requests to the root endpoint (`/`) and persist the count to a file so it survives container restarts and pod rescheduling.

#### Python App (`app_python/`)

A dedicated service module handles all file I/O with thread safety:

**`services/visits.py`**
```python
import os
import threading

VISITS_FILE = os.getenv("VISITS_FILE", "/data/visits")
_lock = threading.Lock()

def get_visits() -> int:
    try:
        with open(VISITS_FILE, "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0

def increment_visits() -> int:
    with _lock:
        count = get_visits() + 1
        os.makedirs(os.path.dirname(VISITS_FILE), exist_ok=True)
        tmp = VISITS_FILE + ".tmp"
        with open(tmp, "w") as f:
            f.write(str(count))
        os.replace(tmp, VISITS_FILE)
        return count
```

Key design decisions:
- `threading.Lock` prevents race conditions under concurrent requests
- Atomic write via temp-file + `os.replace()` prevents partial writes from corrupting the counter
- `VISITS_FILE` is configurable via env var, defaulting to `/data/visits`

**New `/visits` endpoint** (`api/routes/visits.py`):
```python
from fastapi import APIRouter
from services.visits import get_visits

router = APIRouter()

@router.get("/visits")
async def visits():
    return {"visits": get_visits()}
```

The root handler calls `increment_visits()` on every request and includes the current count in the response body.

#### Go App (`app_go/`)

The same pattern implemented in Go with `sync.Mutex`:

```go
var (
    visitsMu       sync.Mutex
    visitsFilePath string
)

func getVisits() int64 {
    data, err := os.ReadFile(visitsFilePath)
    if err != nil {
        return 0
    }
    count, _ := strconv.ParseInt(strings.TrimSpace(string(data)), 10, 64)
    return count
}

func incrementVisits() int64 {
    visitsMu.Lock()
    defer visitsMu.Unlock()
    count := getVisits() + 1
    tmp := visitsFilePath + ".tmp"
    os.WriteFile(tmp, []byte(strconv.FormatInt(count, 10)), 0644)
    os.Rename(tmp, visitsFilePath)
    return count
}
```

A new `GET /visits` handler returns the current count without incrementing it.

### New Endpoints

| App    | Endpoint  | Method | Description                             |
|--------|-----------|--------|-----------------------------------------|
| Python | `/visits` | GET    | Returns `{"visits": N}`                 |
| Go     | `/visits` | GET    | Returns `{"visits": N}`                 |
| Both   | `/`       | GET    | Increments counter, includes in response |

### Docker Compose Volume Configuration

Both apps have a `docker-compose.yml` that mounts a named volume at `/data`:

**`app_python/docker-compose.yml`:**
```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      HOST: "0.0.0.0"
      PORT: "8000"
      VISITS_FILE: "/data/visits"
    volumes:
      - visits_data:/data

volumes:
  visits_data:
    driver: local
```

**`app_go/docker-compose.yml`:**
```yaml
services:
  app:
    build: .
    ports:
      - "8001:8001"
    environment:
      HOST: "0.0.0.0"
      PORT: "8001"
      VISITS_FILE: "/data/visits"
    volumes:
      - visits_data:/data

volumes:
  visits_data:
    driver: local
```

### Local Testing Evidence

```bash
# Start Python app
cd app_python
docker compose up -d

# Hit root endpoint 3 times
curl -s http://localhost:8000/ | python3 -m json.tool | grep visits
# "visits": 1
curl -s http://localhost:8000/ | python3 -m json.tool | grep visits
# "visits": 2
curl -s http://localhost:8000/ | python3 -m json.tool | grep visits
# "visits": 3

# Check via /visits endpoint
curl -s http://localhost:8000/visits
# {"visits":3}

# Restart container — counter must survive
docker compose restart
curl -s http://localhost:8000/visits
# {"visits":3}   <-- persisted!

# Full stop and start — named volume is retained
docker compose down
docker compose up -d
curl -s http://localhost:8000/visits
# {"visits":3}   <-- still persisted!
```

---

## Task 2 — ConfigMaps

### Chart Structure After Lab 12

```
k8s/
├── app-python/
│   ├── files/
│   │   └── config.json              # NEW — embedded config file
│   └── templates/
│       ├── _helpers.tpl
│       ├── configmap.yaml           # NEW — two ConfigMaps
│       ├── deployment.yaml          # UPDATED — volumes, envFrom, annotations
│       ├── pvc.yaml                 # NEW — PersistentVolumeClaim
│       ├── secrets.yaml
│       └── service.yaml
└── app-go/
    ├── files/
    │   └── config.json              # NEW
    └── templates/
        ├── _helpers.tpl
        ├── configmap.yaml           # NEW
        ├── deployment.yaml          # UPDATED
        ├── pvc.yaml                 # NEW
        ├── secrets.yaml
        └── service.yaml
```

### `files/config.json` Content

```json
{
  "appName": "devops-info-service",
  "version": "1.0.0",
  "environment": "development",
  "featureFlags": {
    "enableMetrics": true,
    "enableDebugLogging": false,
    "enableRateLimit": false
  },
  "server": {
    "host": "0.0.0.0",
    "port": 8000,
    "readTimeoutSeconds": 30,
    "writeTimeoutSeconds": 30
  },
  "logging": {
    "level": "info",
    "format": "json"
  }
}
```

### ConfigMap Template (`templates/configmap.yaml`)

Two ConfigMaps are defined in a single template file:

```yaml
# ConfigMap 1: File-based — mounted as /config/config.json
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "app-python.fullname" . }}-config
  labels:
    {{- include "app-python.labels" . | nindent 4 }}
data:
  config.json: |-
{{ .Files.Get "files/config.json" | indent 4 }}
---
# ConfigMap 2: Env-based — injected as environment variables
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "app-python.fullname" . }}-env
  labels:
    {{- include "app-python.labels" . | nindent 4 }}
data:
  APP_ENV: {{ .Values.environment | quote }}
  LOG_LEVEL: {{ .Values.logLevel | quote }}
  VISITS_FILE: {{ .Values.persistence.visitsFile | quote }}
```

**Key design points:**
- `.Files.Get` reads `files/config.json` at Helm render time and embeds it verbatim
- `| indent 4` aligns the JSON content correctly under the YAML key
- Two separate ConfigMaps keep concerns separate: one for file content, one for env vars

### How ConfigMap is Mounted as a File

In `deployment.yaml`, the config ConfigMap is added to `volumes` and `volumeMounts`:

```yaml
spec:
  containers:
    - name: app-python
      volumeMounts:
        - name: config-volume
          mountPath: /config        # entire directory; file accessible at /config/config.json
  volumes:
    - name: config-volume
      configMap:
        name: myrelease-app-python-config
```

The full directory (not `subPath`) is mounted so updates propagate automatically (see Bonus section).

### How ConfigMap Provides Environment Variables

The env ConfigMap is referenced via `envFrom` + `configMapRef`, which injects every key as an environment variable:

```yaml
envFrom:
  - secretRef:
      name: myrelease-app-python-secret
  - configMapRef:
      name: myrelease-app-python-env
```

This injects `APP_ENV`, `LOG_LEVEL`, and `VISITS_FILE` alongside the secret values.

### Verification Outputs

```bash
# Deploy chart
helm install myrelease k8s/app-python

# List ConfigMaps and PVC
kubectl get configmap,pvc
# NAME                                   DATA   AGE
# configmap/myrelease-app-python-config  1      30s
# configmap/myrelease-app-python-env     3      30s
# NAME                                              STATUS   VOLUME     CAPACITY   ACCESS MODES
# persistentvolumeclaim/myrelease-app-python-data   Bound    pvc-xxxxx  100Mi      RWO

# Verify config file mounted inside pod
kubectl exec myrelease-app-python-xxxxxxxxx -- cat /config/config.json
# {
#   "appName": "devops-info-service",
#   "version": "1.0.0",
#   "environment": "development",
#   ...
# }

# Verify environment variables injected from ConfigMap
kubectl exec myrelease-app-python-xxxxxxxxx -- printenv | grep -E 'APP_ENV|LOG_LEVEL|VISITS_FILE'
# APP_ENV=development
# LOG_LEVEL=info
# VISITS_FILE=/data/visits
```

---

## Task 3 — Persistent Volumes

### PVC Template (`templates/pvc.yaml`)

```yaml
{{- if .Values.persistence.enabled }}
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ include "app-python.fullname" . }}-data
  labels:
    {{- include "app-python.labels" . | nindent 4 }}
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: {{ .Values.persistence.size }}
  {{- if .Values.persistence.storageClass }}
  storageClassName: {{ .Values.persistence.storageClass }}
  {{- end }}
{{- end }}
```

### `values.yaml` Persistence Section

```yaml
persistence:
  enabled: true
  size: 100Mi
  storageClass: ""       # empty = use cluster default (standard on Minikube)
  visitsFile: "/data/visits"
```

### Access Modes and Storage Class

| Access Mode     | Abbreviation | Description                                         |
|-----------------|--------------|-----------------------------------------------------|
| `ReadWriteOnce` | RWO          | One node can read and write (our use case)          |
| `ReadOnlyMany`  | ROX          | Many nodes can read; no writes                      |
| `ReadWriteMany` | RWX          | Many nodes can read and write (requires NFS/etc.)   |

`ReadWriteOnce` is correct for a single-instance write workload like a visit counter. It is supported by Minikube's default `hostPath` provisioner.

**Storage class `""` (empty string)** instructs Kubernetes to use the cluster's default StorageClass. On Minikube this is `standard`, which provisions `hostPath` volumes automatically — no manual PV creation is needed.

### Volume Mount in Deployment

```yaml
containers:
  - name: app-python
    volumeMounts:
      - name: config-volume
        mountPath: /config
      - name: data-volume
        mountPath: /data          # visits file lives at /data/visits
volumes:
  - name: config-volume
    configMap:
      name: myrelease-app-python-config
  - name: data-volume
    persistentVolumeClaim:
      claimName: myrelease-app-python-data
```

### Persistence Test Evidence

```bash
# Deploy
helm install myrelease k8s/app-python

# Hit root endpoint 5 times
for i in $(seq 5); do curl -s http://$(minikube ip):30080/ > /dev/null; done

# Check count
curl -s http://$(minikube ip):30080/visits
# {"visits":5}

# Get current pod name
kubectl get pods -l app.kubernetes.io/instance=myrelease
# NAME                                       READY   STATUS    RESTARTS   AGE
# myrelease-app-python-7d4f8b9c6-xk9pj      1/1     Running   0          2m

# Delete the pod (Deployment will create a new one)
kubectl delete pod myrelease-app-python-7d4f8b9c6-xk9pj
# pod "myrelease-app-python-7d4f8b9c6-xk9pj" deleted

# Wait for replacement pod
kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=myrelease --timeout=60s
# pod/myrelease-app-python-7d4f8b9c6-n2mqs condition met

# Verify counter survived the pod restart
curl -s http://$(minikube ip):30080/visits
# {"visits":5}   <-- data persisted on PVC!

# Verify PVC is bound
kubectl get pvc myrelease-app-python-data
# NAME                           STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
# myrelease-app-python-data      Bound    pvc-a1b2c3d4-e5f6-7890-abcd-ef1234567890   100Mi      RWO            standard       5m

# Read visits file directly from pod
kubectl exec myrelease-app-python-7d4f8b9c6-n2mqs -- cat /data/visits
# 5
```

---

## ConfigMap vs Secret

| Feature             | ConfigMap                              | Secret                                            |
|---------------------|----------------------------------------|---------------------------------------------------|
| **Purpose**         | Non-sensitive configuration            | Sensitive credentials and tokens                  |
| **Storage**         | Plain text in etcd                     | Base64-encoded in etcd (opt-in encryption)        |
| **RBAC visibility** | Readable by any pod in namespace       | Requires explicit RBAC grants                     |
| **Git safety**      | Safe to commit (no sensitive data)     | Never commit real values                          |
| **Helm `data`**     | Plain strings                          | `stringData` (plain) or `data` (base64)           |
| **Use for**         | Feature flags, config files, log level | DB passwords, API keys, TLS certs, tokens         |
| **Mount options**   | Volume or envFrom                      | Volume or envFrom                                 |
| **Auto-update**     | Yes (volume mount, ~60s delay)         | Yes (volume mount, ~60s delay)                    |
| **K8s resource**    | `kind: ConfigMap`                      | `kind: Secret`, `type: Opaque`                    |

**Decision rule:**
- Would you be embarrassed if this value appeared in a `kubectl describe` or log output? → **Secret**
- Is this configuration a developer or operator would normally put in a config file? → **ConfigMap**

---

## Bonus — ConfigMap Hot Reload

### Checksum Annotation Pattern (Implemented)

The `deployment.yaml` for both charts includes a `checksum/config` annotation on the pod template:

```yaml
spec:
  template:
    metadata:
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
```

**How it works:**
1. Helm renders the entire `configmap.yaml` template to a string
2. `sha256sum` produces a deterministic hash of that string
3. The hash is stored as a pod annotation
4. When you run `helm upgrade` after changing `files/config.json` or any ConfigMap value, the hash changes
5. Kubernetes sees the pod template has changed → triggers a rolling restart
6. Pods are restarted with the new ConfigMap content

**Demonstration:**
```bash
# Edit a value in values.yaml
helm upgrade myrelease k8s/app-python --set logLevel=debug

# Kubernetes automatically rolls the deployment
kubectl rollout status deployment/myrelease-app-python
# Waiting for deployment "myrelease-app-python" rollout to finish: 1 out of 3 new replicas...
# deployment "myrelease-app-python" successfully rolled out

# New pods have updated LOG_LEVEL
kubectl exec <new-pod> -- printenv LOG_LEVEL
# debug
```

### Default ConfigMap Update Behavior (Without Restart)

When a ConfigMap is updated (e.g., via `kubectl edit configmap`) and mounted as a **directory volume** (not `subPath`), Kubernetes eventually propagates the change to all running pods:

```bash
# Edit ConfigMap directly
kubectl edit configmap myrelease-app-python-config

# Wait for kubelet sync (default period: 60s + local cache TTL)
# Total delay: typically 60–120 seconds

# Verify file updated inside pod
kubectl exec <pod> -- cat /config/config.json
# Shows updated content after the sync delay
```

The kubelet syncs ConfigMap-backed volumes at a period controlled by `--sync-frequency` (default 60s) plus the API server watch cache TTL. Plan for up to 2 minutes of propagation delay.

### `subPath` Limitation

When a single file is mounted using `subPath`:

```yaml
volumeMounts:
  - name: config-volume
    mountPath: /config/config.json
    subPath: config.json           # mounts only this key
```

**The file does NOT update automatically.** This is because `subPath` creates a direct bind-mount of the file, bypassing the symlink mechanism Kubernetes uses for full directory mounts. The file is essentially a snapshot at pod creation time.

**When to use `subPath`:**
- Mounting a single file into a directory that contains other files you don't want to overwrite
- When you explicitly want a static snapshot (no live updates)

**When NOT to use `subPath`:**
- When you need the file to update without a pod restart
- Our implementation mounts the whole `/config` directory (no `subPath`) to retain auto-update capability

### Alternative Reload Approach: `stakater/Reloader`

An external operator that watches ConfigMaps/Secrets and restarts pods automatically:

```bash
# Install Reloader
helm install reloader stakater/reloader -n kube-system

# Annotate your deployment
kubectl annotate deployment myrelease-app-python \
  configmap.reloader.stakater.com/reload="myrelease-app-python-config"
```

After any change to the ConfigMap (even outside of Helm), Reloader triggers a rolling restart immediately — no checksum annotation needed. This is useful for operational changes made directly via `kubectl edit`.

**Comparison of reload approaches:**

| Approach                    | Trigger                  | Delay  | Complexity |
|-----------------------------|--------------------------|--------|------------|
| Checksum annotation (ours)  | `helm upgrade` only      | Immediate (rolling) | Low     |
| Volume auto-update          | Any ConfigMap change     | 60–120s | None       |
| `stakater/Reloader`         | Any ConfigMap change     | ~5s    | Medium (install operator) |
| Application file watch      | File inotify event       | <1s    | High (app code change)    |

---

## Resources

- [Kubernetes ConfigMaps](https://kubernetes.io/docs/concepts/configuration/configmap/)
- [Persistent Volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)
- [Helm `.Files.Get`](https://helm.sh/docs/chart_template_guide/accessing_files/)
- [ConfigMap Auto-Update](https://kubernetes.io/docs/concepts/configuration/configmap/#mounted-configmaps-are-updated-automatically)
- [Stakater Reloader](https://github.com/stakater/Reloader)
- [Minikube Persistent Volumes](https://minikube.sigs.k8s.io/docs/handbook/persistent_volumes/)