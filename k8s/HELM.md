# Helm Chart Documentation

## Chart Overview

### Chart Structure

```
k8s/
├── app-python/                  # Main Python application chart
│   ├── Chart.yaml               # Chart metadata (name, version, dependencies)
│   ├── values.yaml              # Default configuration values
│   ├── values-dev.yaml          # Development environment overrides
│   ├── values-prod.yaml         # Production environment overrides
│   ├── charts/                  # Packaged chart dependencies
│   └── templates/
│       ├── _helpers.tpl         # Reusable template helpers (names, labels)
│       ├── deployment.yaml      # Kubernetes Deployment template
│       ├── service.yaml         # Kubernetes Service template
│       ├── NOTES.txt            # Post-install usage instructions
│       └── hooks/
│           ├── pre-install-job.yaml   # Pre-install validation hook
│           └── post-install-job.yaml  # Post-install smoke test hook
├── app-go/                      # Go application chart (bonus)
│   ├── Chart.yaml
│   ├── values.yaml
│   ├── charts/
│   └── templates/
│       ├── _helpers.tpl
│       ├── deployment.yaml
│       ├── service.yaml
│       └── NOTES.txt
├── common-lib/                  # Shared library chart (bonus)
│   ├── Chart.yaml
│   └── templates/
│       └── _labels.tpl          # Common name/label helpers
├── deployment.yml               # Original Lab 9 manifest
└── service.yml                  # Original Lab 9 manifest
```

### Key Template Files

| File | Purpose |
|------|---------|
| `_helpers.tpl` | Defines reusable named templates for names, fullnames, chart labels, and selector labels |
| `deployment.yaml` | Templatized Deployment resource — replicas, image, resources, probes all driven by values |
| `service.yaml` | Templatized Service resource — type, ports, nodePort all configurable |
| `hooks/pre-install-job.yaml` | Job that validates environment before installation |
| `hooks/post-install-job.yaml` | Job that runs smoke tests after installation |

### Values Organization

Values are organized hierarchically by concern:
- `image.*` — container image settings (repository, tag, pullPolicy)
- `service.*` — service exposure (type, port, targetPort, nodePort)
- `resources.*` — CPU and memory requests/limits
- `strategy.*` — deployment rollout strategy
- `livenessProbe.*` / `readinessProbe.*` — health check configuration
- `replicaCount` — number of pod replicas

---

## Configuration Guide

### Important Values

| Value | Default | Description |
|-------|---------|-------------|
| `replicaCount` | `3` | Number of pod replicas |
| `image.repository` | `essence666/app_python_lab_2` | Docker image repository |
| `image.tag` | `latest` | Docker image tag |
| `image.pullPolicy` | `IfNotPresent` | Image pull policy |
| `service.type` | `NodePort` | Kubernetes service type |
| `service.port` | `80` | Service port |
| `service.targetPort` | `8000` | Container port |
| `service.nodePort` | `30080` | NodePort (only for NodePort type) |
| `resources.requests.cpu` | `100m` | CPU request |
| `resources.requests.memory` | `128Mi` | Memory request |
| `resources.limits.cpu` | `200m` | CPU limit |
| `resources.limits.memory` | `256Mi` | Memory limit |

### Environment Customization

**Development** (`values-dev.yaml`):
- 1 replica (minimal footprint)
- Relaxed resource limits (50m CPU, 64Mi memory requests)
- Faster probe startup (5s liveness, 3s readiness)
- NodePort service type

**Production** (`values-prod.yaml`):
- 5 replicas (high availability)
- Generous resource limits (200m CPU, 256Mi memory requests)
- Conservative probe startup (30s liveness, 10s readiness)
- LoadBalancer service type
- Pinned image tag (`1.0.0` instead of `latest`)
- `Always` pull policy to ensure fresh images

### Example Installations

```bash
# Default values
helm install myapp k8s/app-python

# Development environment
helm install myapp-dev k8s/app-python -f k8s/app-python/values-dev.yaml

# Production environment
helm install myapp-prod k8s/app-python -f k8s/app-python/values-prod.yaml

# Override specific value
helm install myapp k8s/app-python --set replicaCount=10

# Combine values file with overrides
helm install myapp k8s/app-python -f k8s/app-python/values-prod.yaml --set image.tag="2.0.0"
```

---

## Hook Implementation

### Hooks Overview

Two lifecycle hooks are implemented as Kubernetes Jobs:

| Hook | Type | Weight | Deletion Policy | Purpose |
|------|------|--------|-----------------|---------|
| `pre-install-job` | `pre-install` | `-5` | `hook-succeeded` | Validates environment readiness before installing resources |
| `post-install-job` | `post-install` | `5` | `hook-succeeded` | Runs smoke tests after all resources are deployed |

### Execution Order

1. **Pre-install hook** (weight `-5`) runs first — validates that the environment is ready
2. Main chart resources (Deployment, Service) are created
3. **Post-install hook** (weight `5`) runs last — verifies deployment health

### Deletion Policies

Both hooks use `hook-succeeded` policy, meaning:
- Jobs are automatically deleted after successful completion
- Failed jobs are kept for debugging
- This prevents accumulation of completed Job resources in the cluster

### Hook Verification

```bash
# Watch hooks during install
helm install myrelease k8s/app-python
kubectl get jobs -w
kubectl get pods -w

# Check hook logs
kubectl logs job/myrelease-app-python-pre-install
kubectl logs job/myrelease-app-python-post-install

# Verify hooks cleaned up after success
kubectl get jobs  # Should not show hook jobs
```

---

## Installation Evidence

### Helm Lint

```bash
$ helm lint k8s/app-python
==> Linting k8s/app-python
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### Helm Template (Dry Run)

```bash
$ helm template test-release k8s/app-python
```

Renders all templates with default values — Deployment with 3 replicas,
NodePort Service on port 30080, plus pre/post-install hook Jobs.

### Installation Commands

```bash
# Install with default values
$ helm install myrelease k8s/app-python

# Verify release
$ helm list
NAME        NAMESPACE   REVISION    STATUS      CHART               APP VERSION
myrelease   default     1           deployed    app-python-0.1.0    1.0

# Check deployed resources
$ kubectl get all -l app.kubernetes.io/instance=myrelease
```

### Dev vs Prod Deployment

```bash
# Development
$ helm install myapp-dev k8s/app-python -f k8s/app-python/values-dev.yaml
# -> 1 replica, NodePort, relaxed resources

# Production
$ helm install myapp-prod k8s/app-python -f k8s/app-python/values-prod.yaml
# -> 5 replicas, LoadBalancer, generous resources, pinned tag
```

---

## Operations

### Install

```bash
helm install <release-name> k8s/app-python [-f <values-file>]
```

### Upgrade

```bash
# Upgrade with new values
helm upgrade myrelease k8s/app-python -f k8s/app-python/values-prod.yaml

# Upgrade with specific overrides
helm upgrade myrelease k8s/app-python --set image.tag="2.0.0"
```

### Rollback

```bash
# View release history
helm history myrelease

# Rollback to previous revision
helm rollback myrelease

# Rollback to specific revision
helm rollback myrelease 1
```

### Uninstall

```bash
helm uninstall myrelease
```

---

## Testing & Validation

### Lint

```bash
helm lint k8s/app-python
```

### Template Rendering

```bash
# Render with default values
helm template test-release k8s/app-python

# Render with dev values
helm template test-release k8s/app-python -f k8s/app-python/values-dev.yaml

# Render with prod values
helm template test-release k8s/app-python -f k8s/app-python/values-prod.yaml
```

### Dry Run

```bash
helm install --dry-run --debug test-release k8s/app-python
```

### Application Accessibility

```bash
# For NodePort
export NODE_IP=$(kubectl get nodes -o jsonpath="{.items[0].status.addresses[0].address}")
curl http://$NODE_IP:30080/health

# For LoadBalancer
export SERVICE_IP=$(kubectl get svc myrelease-app-python -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl http://$SERVICE_IP:80/health
```

---

## Bonus: Library Charts

### Overview

A shared library chart (`common-lib`) provides common template helpers used by both `app-python` and `app-go` charts, eliminating duplication.

### Library Chart Structure

```
k8s/common-lib/
├── Chart.yaml          # type: library
└── templates/
    └── _labels.tpl     # Shared named templates
```

### Shared Templates

The library chart defines these reusable templates:
- `common.name` — chart name with override support
- `common.fullname` — fully qualified release name
- `common.chart` — chart name + version label
- `common.labels` — standard Kubernetes labels (helm.sh/chart, app version, managed-by)
- `common.selectorLabels` — minimal labels for pod selection

### Usage in Application Charts

Both `app-python` and `app-go` declare the library as a dependency in `Chart.yaml`:

```yaml
dependencies:
  - name: common-lib
    version: 0.1.0
    repository: "file://../common-lib"
```

Build dependencies before install:

```bash
helm dependency update k8s/app-python
helm dependency update k8s/app-go

helm install python-release k8s/app-python
helm install go-release k8s/app-go
```

### Benefits

- **DRY**: Label and naming logic defined once, used everywhere
- **Consistency**: All charts produce identical label structures
- **Maintainability**: Update labels in one place, all charts get the change
- **Scalability**: Adding a new app chart only requires importing the library
