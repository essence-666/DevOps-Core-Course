# GitOps with ArgoCD Documentation

## Overview

This document covers the Lab 13 implementation: installing ArgoCD, deploying applications via declarative manifests, configuring multi-environment deployments, and testing self-healing behaviour.

---

## Task 1 — ArgoCD Installation & Setup

### Installation via Helm

```bash
# Add the Argo Helm repository
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

# Create a dedicated namespace
kubectl create namespace argocd

# Install ArgoCD
helm install argocd argo/argo-cd \
  --namespace argocd \
  --set server.service.type=NodePort

# Wait for all pods to become Ready
kubectl wait --for=condition=ready pod \
  -l app.kubernetes.io/name=argocd-server \
  -n argocd \
  --timeout=120s
```

### Verifying Installation

```bash
kubectl get pods -n argocd
```

```
NAME                                                READY   STATUS    RESTARTS   AGE
argocd-application-controller-0                     1/1     Running   0          2m
argocd-applicationset-controller-xxxxxxxxx-xxxxx    1/1     Running   0          2m
argocd-dex-server-xxxxxxxxx-xxxxx                   1/1     Running   0          2m
argocd-notifications-controller-xxxxxxxxx-xxxxx     1/1     Running   0          2m
argocd-redis-xxxxxxxxx-xxxxx                        1/1     Running   0          2m
argocd-repo-server-xxxxxxxxx-xxxxx                  1/1     Running   0          2m
argocd-server-xxxxxxxxx-xxxxx                       1/1     Running   0          2m
```

### Accessing the UI

```bash
# Port-forward the ArgoCD server (keep terminal open)
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Retrieve the initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d && echo

# Open browser at https://localhost:8080
# Username: admin
# Password: <from command above>
```

### CLI Installation and Login

```bash
# macOS
brew install argocd

# Log in via CLI (after port-forward is running)
argocd login localhost:8080 --insecure \
  --username admin \
  --password <initial-password>

# Verify connection
argocd version
argocd app list
```

```
argocd: v2.13.x
  BuildDate: ...
  GitCommit: ...
  GoVersion: go1.22.x
  ...
server: v2.13.x
```

---

## Task 2 — Application Deployment

### Directory Structure

```
k8s/argocd/
├── application.yaml          # Python app — default namespace, manual sync
├── application-dev.yaml      # Python app — dev namespace, auto-sync
├── application-prod.yaml     # Python app — prod namespace, manual sync
├── application-go.yaml       # Go app — default namespace, manual sync
└── applicationset.yaml       # Bonus: ApplicationSet (list generator)
```

### Application Manifest (`application.yaml`)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: python-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/essence-666/DevOps-Core-Course.git
    targetRevision: master
    path: k8s/app-python
    helm:
      valueFiles:
        - values.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: default
  syncPolicy:
    syncOptions:
      - CreateNamespace=true
      - PrunePropagationPolicy=foreground
      - PruneLast=true
```

**Key fields explained:**

| Field | Value | Purpose |
|-------|-------|---------|
| `repoURL` | GitHub repo URL | ArgoCD clones this repo to track desired state |
| `targetRevision` | `master` | Branch or tag to watch |
| `path` | `k8s/app-python` | Directory containing the Helm chart |
| `destination.server` | `https://kubernetes.default.svc` | In-cluster deployment |
| `destination.namespace` | `default` | Target Kubernetes namespace |
| No `automated` block | — | Manual sync — operator must approve each deployment |

### Deploying and Syncing

```bash
# Apply the Application manifest
kubectl apply -f k8s/argocd/application.yaml

# Check application status (OutOfSync until first sync)
argocd app get python-app
```

```
Name:               argocd/python-app
Project:            default
Server:             https://kubernetes.default.svc
Namespace:          default
URL:                https://localhost:8080/applications/python-app
Source:
  Repo:             https://github.com/essence-666/DevOps-Core-Course.git
  Target:           master
  Path:             k8s/app-python
SyncStatus:         OutOfSync from master
HealthStatus:       Missing

GROUP  KIND        NAMESPACE  NAME             STATUS     HEALTH   HOOK  MESSAGE
       Service     default    python-app       OutOfSync  Missing
apps   Deployment  default    python-app       OutOfSync  Missing
```

```bash
# Trigger initial sync
argocd app sync python-app

# Watch deployment progress
kubectl rollout status deployment -n default -l app.kubernetes.io/instance=python-app
```

```
Waiting for deployment "python-app-app-python" rollout to finish: 0 of 3 updated...
Waiting for deployment rollout to finish: 1 out of 3 new replicas have been updated...
Waiting for deployment rollout to finish: 2 out of 3 new replicas have been updated...
deployment "python-app-app-python" successfully rolled out
```

```bash
# Final status — should show Synced + Healthy
argocd app get python-app
```

```
SyncStatus:   Synced to master (abc1234)
HealthStatus: Healthy
```

### GitOps Workflow Test

```bash
# Make a change — update replica count in values.yaml
# git commit and push...

# ArgoCD detects drift (polls every 3 minutes, or use webhook)
argocd app get python-app
# SyncStatus: OutOfSync from master

# View the diff
argocd app diff python-app
# --- current
# +++ target
# @@ -5,7 +5,7 @@
# -  replicas: 3
# +  replicas: 4

# Apply the change
argocd app sync python-app
```

---

## Task 3 — Multi-Environment Deployment

### Environment Overview

| Environment | Namespace | Sync Policy | Values File | Replicas | Resources |
|-------------|-----------|-------------|-------------|----------|-----------|
| Default | `default` | Manual | `values.yaml` | 3 | Standard |
| Dev | `dev` | **Auto** (selfHeal + prune) | `values-dev.yaml` | 1 | Minimal |
| Prod | `prod` | **Manual** | `values-prod.yaml` | 5 | Generous |

### Create Namespaces

```bash
kubectl create namespace dev
kubectl create namespace prod
```

### Dev Application (`application-dev.yaml`)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: python-app-dev
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/essence-666/DevOps-Core-Course.git
    targetRevision: master
    path: k8s/app-python
    helm:
      valueFiles:
        - values.yaml
        - values-dev.yaml      # overrides: 1 replica, relaxed limits, NodePort
  destination:
    server: https://kubernetes.default.svc
    namespace: dev
  syncPolicy:
    automated:
      prune: true       # delete resources removed from Git
      selfHeal: true    # revert manual cluster changes
    syncOptions:
      - CreateNamespace=true
      - ServerSideApply=true
```

**Dev-specific values (`values-dev.yaml`):**
- `replicaCount: 1` — minimal footprint
- `resources.limits.cpu: 100m`, `memory: 128Mi` — low overhead
- `service.type: NodePort` — direct access in local cluster

### Prod Application (`application-prod.yaml`)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: python-app-prod
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/essence-666/DevOps-Core-Course.git
    targetRevision: master
    path: k8s/app-python
    helm:
      valueFiles:
        - values.yaml
        - values-prod.yaml     # overrides: 5 replicas, generous limits, LoadBalancer
  destination:
    server: https://kubernetes.default.svc
    namespace: prod
  syncPolicy:
    syncOptions:
      - CreateNamespace=true
      - PrunePropagationPolicy=foreground
      - PruneLast=true
    # No automated block — prod requires explicit manual approval
```

**Prod-specific values (`values-prod.yaml`):**
- `replicaCount: 5` — high availability
- `resources.limits.cpu: 500m`, `memory: 512Mi` — production grade
- `image.pullPolicy: Always` — ensures fresh image
- `image.tag: 1.0.0` — pinned tag (never `latest` in prod)
- `service.type: LoadBalancer`

### Deploying Both Environments

```bash
kubectl apply -f k8s/argocd/application-dev.yaml
kubectl apply -f k8s/argocd/application-prod.yaml

# Dev syncs automatically
# Prod requires manual sync:
argocd app sync python-app-prod
```

### Verification

```bash
argocd app list
```

```
NAME              CLUSTER                         NAMESPACE  PROJECT  STATUS  HEALTH   SYNCPOLICY  CONDITIONS
python-app        https://kubernetes.default.svc  default    default  Synced  Healthy  Manual      <none>
python-app-dev    https://kubernetes.default.svc  dev        default  Synced  Healthy  Auto-Prune  <none>
python-app-prod   https://kubernetes.default.svc  prod       default  Synced  Healthy  Manual      <none>
```

```bash
# Verify pods in each namespace
kubectl get pods -n dev
# NAME                                     READY   STATUS    RESTARTS   AGE
# python-app-dev-app-python-xxxxxxx-xxxxx  1/1     Running   0          1m

kubectl get pods -n prod
# NAME                                      READY   STATUS    RESTARTS   AGE
# python-app-prod-app-python-xxxxxxx-xxxxx  1/1     Running   0          1m
# python-app-prod-app-python-xxxxxxx-yyyyy  1/1     Running   0          1m
# python-app-prod-app-python-xxxxxxx-zzzzz  1/1     Running   0          1m
# python-app-prod-app-python-xxxxxxx-aaaaa  1/1     Running   0          1m
# python-app-prod-app-python-xxxxxxx-bbbbb  1/1     Running   0          1m
```

### Why Manual Sync for Production?

| Reason | Explanation |
|--------|-------------|
| **Change review** | Every prod deployment should pass a human review or approval gate |
| **Controlled timing** | Deploy during maintenance windows, not instantly on every commit |
| **Compliance** | Regulated environments require audit trail of who approved each release |
| **Rollback planning** | Operator can prepare rollback steps before pressing sync |
| **Staged rollout** | Deploy to dev → verify → promote to prod |

---

## Task 4 — Self-Healing & Sync Policies

### Test 1 — Manual Scale (ArgoCD Self-Healing)

Dev has `selfHeal: true`, so any manual cluster changes are reverted to match Git.

```bash
# Before: dev has 1 replica (from values-dev.yaml)
kubectl get pods -n dev
# NAME                                    READY   STATUS    RESTARTS   AGE
# python-app-dev-app-python-xxxxx-xxxxx   1/1     Running   0          5m

# Manually scale to 5 replicas
kubectl scale deployment -n dev \
  $(kubectl get deploy -n dev -o name) \
  --replicas=5

# Observe the pods scaling up
kubectl get pods -n dev
# NAME                                    READY   STATUS    RESTARTS   AGE
# python-app-dev-app-python-xxxxx-xxxxx   1/1     Running   0          5m
# python-app-dev-app-python-xxxxx-yyyyy   1/1     Running   0          3s
# python-app-dev-app-python-xxxxx-zzzzz   1/1     Running   0          3s
# python-app-dev-app-python-xxxxx-aaaaa   1/1     Running   0          3s
# python-app-dev-app-python-xxxxx-bbbbb   1/1     Running   0          3s

# ArgoCD detects drift immediately
argocd app get python-app-dev | grep -E 'Status|Health'
# SyncStatus:   OutOfSync from master
# HealthStatus: Healthy

# Within ~30 seconds, ArgoCD self-heals and reverts to 1 replica
kubectl get pods -n dev -w
# python-app-dev-app-python-xxxxx-yyyyy   1/1     Terminating   0   25s
# python-app-dev-app-python-xxxxx-zzzzz   1/1     Terminating   0   25s
# python-app-dev-app-python-xxxxx-aaaaa   1/1     Terminating   0   25s
# python-app-dev-app-python-xxxxx-bbbbb   1/1     Terminating   0   25s

# Back to 1 replica — Git wins
kubectl get pods -n dev
# NAME                                    READY   STATUS    RESTARTS   AGE
# python-app-dev-app-python-xxxxx-xxxxx   1/1     Running   0          6m
```

**Behaviour summary:** ArgoCD's `selfHeal` polling interval is ~5 seconds for detected drifts. Revert completes in under 30 seconds.

### Test 2 — Pod Deletion (Kubernetes Self-Healing)

This tests **Kubernetes** self-healing via the ReplicaSet controller — not ArgoCD.

```bash
# Get the pod name
POD=$(kubectl get pods -n dev -o name | head -1)
echo $POD
# pod/python-app-dev-app-python-xxxxx-xxxxx

# Delete the pod
kubectl delete $POD -n dev
# pod "python-app-dev-app-python-xxxxx-xxxxx" deleted

# Kubernetes immediately schedules a replacement (ReplicaSet ensures desired count)
kubectl get pods -n dev -w
# NAME                                    READY   STATUS              RESTARTS   AGE
# python-app-dev-app-python-xxxxx-xxxxx   1/1     Terminating         0          8m
# python-app-dev-app-python-xxxxx-ccccc   0/1     ContainerCreating   0          1s
# python-app-dev-app-python-xxxxx-ccccc   1/1     Running             0          4s
```

**Key distinction:** ArgoCD was not involved here. The Deployment's ReplicaSet controller noticed the pod count dropped below `1` and scheduled a new pod. ArgoCD's sync status remained **Synced** throughout because the *desired state* (1 replica) was still met.

### Test 3 — Configuration Drift

```bash
# Manually add a label to the deployment (simulates an operator making a "quick fix")
kubectl label deployment -n dev \
  $(kubectl get deploy -n dev -o name | sed 's|deployment.apps/||') \
  hotfix=true

# ArgoCD immediately sees the diff
argocd app diff python-app-dev
```

```
===== apps/Deployment dev/python-app-dev-app-python ======
16c16
<     hotfix: "true"
---
```

```bash
# selfHeal reverts the label within ~30 seconds
kubectl get deployment -n dev \
  $(kubectl get deploy -n dev -o name | sed 's|deployment.apps/||') \
  -o jsonpath='{.metadata.labels}' | python3 -m json.tool
# {
#   "app.kubernetes.io/instance": "python-app-dev",
#   "app.kubernetes.io/managed-by": "Helm",
#   ...
#   // "hotfix" label is gone
# }
```

### Sync Behaviour Reference

| Event | Who responds | Mechanism | Timing |
|-------|-------------|-----------|--------|
| Pod crash / OOMKill | Kubernetes | ReplicaSet controller | Immediate (<5s) |
| Manual `kubectl scale` (dev) | ArgoCD | `selfHeal` polling | ~5–30s |
| Manual `kubectl label` (dev) | ArgoCD | `selfHeal` polling | ~5–30s |
| Git commit changes values | ArgoCD (dev) | `automated` + 3-min poll | ≤3 minutes |
| Git commit changes values | Operator (prod) | Manual `argocd app sync` | When approved |
| Webhook push event | ArgoCD | Git webhook | <5s |

**ArgoCD sync interval:** ArgoCD polls Git repositories every **3 minutes** by default. For faster response, configure a Git webhook to trigger ArgoCD immediately on push:

```bash
# In ArgoCD settings → Webhooks
# GitHub webhook URL: https://<argocd-server>/api/webhook
# Secret: set in argocd-secret
```

---

## Bonus — ApplicationSet

### What is ApplicationSet?

ApplicationSet is an ArgoCD controller that generates multiple `Application` resources from a single template. It replaces the need to maintain separate `application-dev.yaml`, `application-prod.yaml`, etc., making it ideal for:

- **Multi-environment** deployments from one template
- **Multi-cluster** deployments
- **Mono-repo** with many microservices

### Implementation — List Generator

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: python-app-set
  namespace: argocd
spec:
  goTemplate: true
  goTemplateOptions: ["missingkey=error"]
  generators:
    - list:
        elements:
          - env: dev
            namespace: dev
            valuesFile: values-dev.yaml
            autoSync: "true"
          - env: prod
            namespace: prod
            valuesFile: values-prod.yaml
            autoSync: "false"
  template:
    metadata:
      name: 'python-app-{{.env}}'
    spec:
      project: default
      source:
        repoURL: https://github.com/essence-666/DevOps-Core-Course.git
        targetRevision: master
        path: k8s/app-python
        helm:
          valueFiles:
            - '{{.valuesFile}}'
      destination:
        server: https://kubernetes.default.svc
        namespace: '{{.namespace}}'
      syncPolicy:
        syncOptions:
          - CreateNamespace=true
  templatePatch: |
    {{- if eq .autoSync "true" -}}
    spec:
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
          - CreateNamespace=true
    {{- end -}}
```

### How It Works

1. The **List generator** iterates over the `elements` array
2. For each element, it substitutes `{{.env}}`, `{{.namespace}}`, `{{.valuesFile}}`, `{{.autoSync}}` into the template
3. This generates two `Application` resources: `python-app-dev` and `python-app-prod`
4. The `templatePatch` block uses Go template conditionals (`goTemplate: true`) to inject the `automated` sync policy only when `autoSync == "true"` — giving dev auto-sync and prod manual sync from a single template

### Deploy the ApplicationSet

```bash
# Remove individual Application manifests if already deployed
argocd app delete python-app-dev
argocd app delete python-app-prod

# Apply the ApplicationSet
kubectl apply -f k8s/argocd/applicationset.yaml

# ArgoCD generates both Applications automatically
argocd app list
```

```
NAME              CLUSTER                         NAMESPACE  PROJECT  STATUS  HEALTH   SYNCPOLICY
python-app-dev    https://kubernetes.default.svc  dev        default  Synced  Healthy  Auto-Prune
python-app-prod   https://kubernetes.default.svc  prod       default  Synced  Healthy  Manual
```

### Git Directory Generator (Optional)

For repos with multiple Helm charts, the Git directory generator auto-discovers all apps:

```yaml
generators:
  - git:
      repoURL: https://github.com/essence-666/DevOps-Core-Course.git
      revision: HEAD
      directories:
        - path: k8s/app-*    # matches k8s/app-python and k8s/app-go
```

This would automatically create an Application for every directory matching `k8s/app-*`, without enumerating them explicitly.

### ApplicationSet vs Individual Applications

| Aspect | Individual Applications | ApplicationSet |
|--------|------------------------|----------------|
| Files to maintain | One per environment | One template for all |
| Adding a new env | Create new YAML file | Add one list element |
| Consistency | Manual (copy-paste errors) | Guaranteed by template |
| Conditional logic | Full YAML flexibility | Requires `goTemplate` or `templatePatch` |
| Visibility | Each app separate | All generated apps linked to the set |
| Deletion | Delete each app | Delete the set (removes all) |
| Best for | Small number of environments | Many environments / clusters |

### Generator Types Reference

| Generator | Use Case |
|-----------|----------|
| **List** | Fixed set of environments or clusters (our case) |
| **Cluster** | Deploy same app to all registered clusters |
| **Git Files** | Parameters defined in JSON/YAML files in the repo |
| **Git Directories** | Auto-discover apps from directory structure |
| **Matrix** | Cross-product of two generators (e.g., all apps × all clusters) |
| **Merge** | Combine multiple generators with overrides |

---

## ArgoCD Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                        ArgoCD Components                        │
│                                                                 │
│  ┌─────────────────┐    ┌──────────────────┐                   │
│  │  argocd-server  │    │   repo-server    │                   │
│  │  (API + UI)     │    │ (git clone +     │                   │
│  └────────┬────────┘    │  helm template)  │                   │
│           │             └────────┬─────────┘                   │
│           │                      │                             │
│  ┌────────▼──────────────────────▼─────────┐                   │
│  │         application-controller          │                   │
│  │  (reconcile loop: desired ↔ actual)     │                   │
│  └────────────────────┬────────────────────┘                   │
│                       │                                        │
└───────────────────────┼────────────────────────────────────────┘
                        │ kubectl apply
           ┌────────────▼───────────────┐
           │      Kubernetes API        │
           ├──────────┬─────────────────┤
           │   dev    │      prod       │
           │ (1 pod)  │   (5 pods)      │
           └──────────┴─────────────────┘
                        ▲
                        │ polls every 3 min
           ┌────────────┴───────────────┐
           │   GitHub: essence-666/     │
           │   DevOps-Core-Course       │
           │   branch: master           │
           └────────────────────────────┘
```

---

## Resources

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [ArgoCD Application CRD](https://argo-cd.readthedocs.io/en/stable/operator-manual/declarative-setup/)
- [Automated Sync Policy](https://argo-cd.readthedocs.io/en/stable/user-guide/auto_sync/)
- [ApplicationSet Documentation](https://argo-cd.readthedocs.io/en/stable/user-guide/application-set/)
- [ApplicationSet Generators](https://argo-cd.readthedocs.io/en/stable/operator-manual/applicationset/Generators/)
- [Sync Options Reference](https://argo-cd.readthedocs.io/en/stable/user-guide/sync-options/)
- [GoTemplates in ApplicationSet](https://argo-cd.readthedocs.io/en/stable/operator-manual/applicationset/GoTemplate/)