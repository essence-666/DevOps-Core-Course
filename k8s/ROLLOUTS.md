# Argo Rollouts — Progressive Delivery

## 1. Argo Rollouts Setup

### Installation

```bash
# Create namespace and install controller
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml

# Install kubectl plugin (macOS)
brew install argoproj/tap/kubectl-argo-rollouts

# Verify
kubectl argo rollouts version
kubectl get pods -n argo-rollouts
```

**Expected output:**
```
NAME                             READY   STATUS    RESTARTS   AGE
argo-rollouts-xxxxxxx-xxxxx      1/1     Running   0          30s
```

### Dashboard

```bash
# Install dashboard
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml

# Access at http://localhost:3100
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

### Rollout vs Deployment — Key Differences

| Field | Deployment | Rollout |
|-------|-----------|---------|
| `apiVersion` | `apps/v1` | `argoproj.io/v1alpha1` |
| `kind` | `Deployment` | `Rollout` |
| `spec.strategy` | `RollingUpdate` / `Recreate` | `canary` / `blueGreen` |
| Traffic shifting | ❌ Not supported | ✅ Weighted percentage |
| Manual promotion | ❌ Not supported | ✅ `pause: {}` |
| Auto-rollback on metrics | ❌ Not supported | ✅ AnalysisTemplate |
| Preview environment | ❌ Not supported | ✅ `previewService` (blueGreen) |

The pod template spec (`spec.template`) is identical between Deployment and Rollout. The Rollout CRD is a drop-in replacement with an extended `spec.strategy` field.

---

## 2. Canary Deployment

### Strategy Configuration

The canary strategy in `values.yaml` defines progressive traffic steps:

```yaml
rollout:
  enabled: true
  strategy: canary
  canary:
    steps:
      - setWeight: 20      # Route 20% traffic to canary
      - pause: {}          # Wait for manual promotion
      - setWeight: 40      # Automatic after promotion
      - pause:
          duration: "30s"  # Auto-advance after 30s
      - setWeight: 60
      - pause:
          duration: "30s"
      - setWeight: 80
      - pause:
          duration: "30s"
      # Implicit setWeight: 100 at end
```

The `pause: {}` (empty pause) halts the rollout indefinitely until a manual `promote` command. Timed pauses advance automatically.

### Deploy and Manage

```bash
# Install / upgrade with canary rollout
helm upgrade --install app-python ./k8s/app-python

# Watch rollout in real time
kubectl argo rollouts get rollout <release-app-python> -w

# Update the image to trigger a new rollout
helm upgrade app-python ./k8s/app-python --set image.tag=v2

# Promote past the manual pause (step 2 → step 3)
kubectl argo rollouts promote <release-app-python>

# Abort and roll back to stable
kubectl argo rollouts abort <release-app-python>

# Retry an aborted rollout
kubectl argo rollouts retry rollout <release-app-python>
```

### Rollout Progression (Dashboard)

The Argo Rollouts dashboard at `http://localhost:3100` shows:

1. **Progressing** — stable pods running, canary pods at 20%
2. **Paused** — waiting for manual promotion (yellow indicator)
3. **Progressing** — traffic advancing 40% → 60% → 80% automatically
4. **Healthy** — 100% traffic on new version, old pods terminating

### Rollback Test

```bash
# Trigger rollout with bad image
helm upgrade app-python ./k8s/app-python --set image.tag=broken

# While paused at 20%, abort the rollout
kubectl argo rollouts abort app-python-app-python

# Traffic shifts immediately back to 0% canary / 100% stable
kubectl argo rollouts get rollout app-python-app-python
# STATUS: Degraded (aborted) — stable revision still serving 100%
```

Rollback during canary is gradual-free: traffic returns to stable immediately on abort.

---

## 3. Blue-Green Deployment

### Strategy Configuration

```yaml
rollout:
  enabled: true
  strategy: blueGreen
  blueGreen:
    autoPromotionEnabled: false   # Require manual promotion
    autoPromotionSeconds: null    # Or set seconds for auto-promote
```

The `values-bluegreen.yaml` file contains these overrides. Apply with:

```bash
helm upgrade --install app-python ./k8s/app-python -f k8s/app-python/values-bluegreen.yaml
```

### Services

Blue-green requires two services:

| Service | Purpose | Source |
|---------|---------|--------|
| `<release-app-python>` | **Active** — production traffic | `service.yaml` |
| `<release-app-python>-preview` | **Preview** — new version for testing | `preview-service.yaml` |

The Rollout controller automatically updates the `selector` on each service when switching blue↔green. The active service selector points to the stable (blue) ReplicaSet; the preview service points to the new (green) ReplicaSet.

### Blue-Green Flow

```bash
# 1. Deploy initial version (blue becomes active)
helm upgrade --install app-python ./k8s/app-python -f k8s/app-python/values-bluegreen.yaml

# 2. Trigger green deployment
helm upgrade app-python ./k8s/app-python \
  -f k8s/app-python/values-bluegreen.yaml \
  --set image.tag=v2

# 3. Watch rollout — green pods start, blue stays active
kubectl argo rollouts get rollout app-python-app-python -w

# 4. Test the new version via preview service
kubectl port-forward svc/app-python-app-python-preview 8081:80
curl http://localhost:8081/health

# 5. Promote green to active (instant traffic switch)
kubectl argo rollouts promote app-python-app-python

# 6. Active service now routes to green; blue pods remain briefly for rollback
```

### Instant Rollback

```bash
# After promotion, roll back to previous revision
kubectl argo rollouts undo app-python-app-python

# Active service selector switches back to blue immediately
# Zero traffic is lost — no gradual shifting needed
```

Blue-green rollback is effectively instantaneous (service selector update), compared to canary rollback which must drain traffic percentages.

---

## 4. Strategy Comparison

### When to Use Canary

- **Gradual confidence building** — expose a small percentage first, monitor errors/latency
- **Long-running requests** — existing connections complete normally on old pods
- **Limited resources** — no need to double replica count
- **Metrics-driven promotion** — combine with AnalysisTemplate to auto-promote when SLOs are met

### When to Use Blue-Green

- **Instant rollback requirement** — production incident recovery in seconds, not minutes
- **Complete pre-production testing** — full environment available via preview service before any production traffic
- **Database schema changes** — both versions run simultaneously, giving time to verify compatibility
- **Stateless services** — works best when sessions aren't pinned to specific pods

### Pros and Cons

| | Canary | Blue-Green |
|--|--------|-----------|
| **Traffic switch** | Gradual (%, controllable) | Instant (all-or-nothing) |
| **Resources** | ~1x (shared) | ~2x during rollout |
| **Rollback speed** | Gradual (drain steps) | Instant (selector swap) |
| **Pre-prod testing** | ❌ Live users see canary | ✅ Preview service |
| **Complexity** | Medium (step config) | Low (two services) |
| **Best for** | Web APIs, gradual SLO validation | Microservices, critical paths |

### Recommendation

- Use **canary** for most web service deployments — lower resource cost and metrics-driven automation make it ideal for continuous delivery pipelines.
- Use **blue-green** when you need pre-production sign-off (e.g., QA team approval) or when instant rollback is a hard requirement (payment services, auth services).

---

## 5. CLI Commands Reference

### Status and Monitoring

```bash
# Get rollout status
kubectl argo rollouts get rollout <name>

# Watch status in real time
kubectl argo rollouts get rollout <name> -w

# List all rollouts in namespace
kubectl argo rollouts list rollouts

# View rollout history
kubectl argo rollouts history rollout <name>
```

### Promotion and Control

```bash
# Promote to next step (or full promotion)
kubectl argo rollouts promote <name>

# Promote fully, skipping all remaining pauses
kubectl argo rollouts promote <name> --full

# Abort current rollout (returns traffic to stable)
kubectl argo rollouts abort <name>

# Retry an aborted or degraded rollout
kubectl argo rollouts retry rollout <name>

# Roll back to previous revision
kubectl argo rollouts undo <name>

# Roll back to specific revision
kubectl argo rollouts undo <name> --to-revision=2
```

### Analysis

```bash
# List analysis runs for a rollout
kubectl get analysisruns -l rollout=<name>

# Get analysis run details
kubectl argo rollouts get analysisrun <name>

# Manually terminate an analysis run
kubectl argo rollouts terminate analysisrun <name>
```

### Dashboard

```bash
# Port-forward to dashboard (http://localhost:3100)
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

---

## 6. Bonus — Automated Analysis

The `analysis-template.yaml` defines a `AnalysisTemplate` that calls the `/health` endpoint to verify the canary pods are healthy before advancing:

```yaml
rollout:
  analysis:
    enabled: true  # Enable in values.yaml to activate
```

The analysis template (`success-rate`) runs 3 health checks at 10-second intervals during the canary phase. If more than 1 check returns a non-`"ok"` status, the rollout is automatically aborted and traffic returns to the stable revision.

```bash
# Enable analysis in canary rollout
helm upgrade app-python ./k8s/app-python --set rollout.analysis.enabled=true

# Deploy a new version — analysis runs automatically after 20% step
helm upgrade app-python ./k8s/app-python \
  --set rollout.analysis.enabled=true \
  --set image.tag=v2

# Simulate failure: deploy version that returns error on /health
# Analysis detects failureLimit exceeded → rollout auto-aborts
kubectl argo rollouts get rollout app-python-app-python
# STATUS: Degraded — auto-rolled back due to failed analysis
```
