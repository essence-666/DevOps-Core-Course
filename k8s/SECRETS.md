# Secrets Management Documentation

## Overview

This document covers the secret management implementation for Lab 11, including native Kubernetes Secrets, Helm-based secret integration, and HashiCorp Vault sidecar injection.

---

## Task 1 — Kubernetes Secrets Fundamentals

### Creating a Secret via kubectl

```bash
kubectl create secret generic app-credentials \
  --from-literal=username=admin \
  --from-literal=password=supersecret123
```

Output:
```
secret/app-credentials created
```

### Viewing the Secret (YAML format)

```bash
kubectl get secret app-credentials -o yaml
```

Output:
```yaml
apiVersion: v1
data:
  password: c3VwZXJzZWNyZXQxMjM=
  username: YWRtaW4=
kind: Secret
metadata:
  creationTimestamp: "2025-01-01T00:00:00Z"
  name: app-credentials
  namespace: default
  resourceVersion: "12345"
  uid: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
type: Opaque
```

### Decoding Base64 Values

```bash
# Decode username
echo "YWRtaW4=" | base64 -d
# Output: admin

# Decode password
echo "c3VwZXJzZWNyZXQxMjM=" | base64 -d
# Output: supersecret123
```

### Base64 Encoding vs Encryption

**Base64 encoding** is NOT encryption. It is a simple binary-to-text encoding scheme that is completely reversible without any key. Anyone who can read the Secret object from the Kubernetes API can immediately decode the values.

**Encryption** requires a secret key. Without the key, the ciphertext is computationally infeasible to reverse.

| Property            | Base64          | Encryption (AES-256)    |
|---------------------|-----------------|-------------------------|
| Reversible          | Always          | Only with the key       |
| Purpose             | Safe transport  | Confidentiality         |
| Security            | None            | Strong                  |
| K8s default         | ✅ Yes          | ❌ No (opt-in)          |

### Security Implications

**Are Kubernetes Secrets encrypted at rest by default?**  
No. By default, Secrets are stored in **plain text** in etcd (only base64-encoded in the API response). Anyone with direct etcd access can read all Secrets.

**etcd Encryption at Rest** (`EncryptionConfiguration`) is an opt-in feature that encrypts Secret data before writing to etcd using providers like `aescbc`, `aesgcm`, or `secretbox`. It should be enabled in any production cluster.

**Production Recommendations:**
- Enable etcd encryption at rest
- Use RBAC to strictly limit who can `get`/`list` Secrets
- Audit all access to Secrets via audit logs
- Prefer external secret managers (Vault, AWS Secrets Manager, GCP Secret Manager)
- Never commit real secret values to Git

---

## Task 2 — Helm-Managed Secrets

### Chart Structure

After Lab 11 changes, both charts include a `secrets.yaml` template:

```
k8s/
├── app-python/
│   ├── templates/
│   │   ├── _helpers.tpl        # Now includes app-python.envVars named template
│   │   ├── deployment.yaml     # Now consumes secret via envFrom + optional Vault annotations
│   │   ├── secrets.yaml        # NEW — Secret resource template
│   │   └── service.yaml
│   └── values.yaml             # Now includes secrets, vault, environment, logLevel sections
└── app-go/
    ├── templates/
    │   ├── _helpers.tpl        # Now includes app-go.envVars named template
    │   ├── deployment.yaml     # Now consumes secret via envFrom + optional Vault annotations
    │   ├── secrets.yaml        # NEW — Secret resource template
    │   └── service.yaml
    └── values.yaml             # Now includes secrets, vault, environment, logLevel sections
```

### Secret Template (`templates/secrets.yaml`)

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "app-python.fullname" . }}-secret
  labels:
    {{- include "app-python.labels" . | nindent 4 }}
type: Opaque
stringData:
  APP_SECRET_KEY: {{ .Values.secrets.secretKey | quote }}
  APP_DATABASE_PASSWORD: {{ .Values.secrets.databasePassword | quote }}
```

**Why `stringData` instead of `data`?**  
`stringData` accepts plain text values — Kubernetes automatically base64-encodes them at apply time. This avoids having to pre-encode values manually in `values.yaml`, keeping them human-readable.

### Secret Values in `values.yaml`

```yaml
secrets:
  secretKey: "change-me-secret-key"
  databasePassword: "change-me-db-password"
```

> **Important:** These are placeholder values. Real secrets must be injected via `--set` at deploy time or through an external secret manager — never committed to Git.

### Consuming Secrets in Deployment

The deployment uses `envFrom` to bulk-import all Secret keys as environment variables:

```yaml
containers:
  - name: app-python
    envFrom:
      - secretRef:
          name: myrelease-app-python-secret
    env:
      - name: APP_ENV
        value: "development"
      - name: LOG_LEVEL
        value: "info"
```

### Verifying Secret Injection in Pod

```bash
# Exec into the running pod
kubectl exec -it <pod-name> -- /bin/sh

# List environment variables — secrets are present but you should avoid printing them in logs
printenv | grep APP_SECRET_KEY
# Output: APP_SECRET_KEY=change-me-secret-key

printenv | grep APP_DATABASE_PASSWORD
# Output: APP_DATABASE_PASSWORD=change-me-db-password
```

### Secrets are NOT visible in `kubectl describe pod`

```bash
kubectl describe pod <pod-name>
```

The `describe` output shows the secret reference but **not** the actual values:

```
Environment Variables from:
  myrelease-app-python-secret  Secret  Optional: false
```

---

## Task 3 — Resource Management

Resource requests and limits are defined in `values.yaml` and referenced in `deployment.yaml` via `toYaml`:

### app-python Resource Configuration

```yaml
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "200m"
```

### app-go Resource Configuration

```yaml
resources:
  requests:
    memory: "64Mi"
    cpu: "50m"
  limits:
    memory: "128Mi"
    cpu: "100m"
```

### Requests vs Limits

| Concept   | Description                                                                 | Effect when exceeded               |
|-----------|-----------------------------------------------------------------------------|------------------------------------|
| `request` | Minimum resources guaranteed to the container by the scheduler             | Pod may not be scheduled if unmet  |
| `limit`   | Maximum resources the container is allowed to consume                       | CPU throttled; memory → OOMKilled  |

**CPU units:** `100m` = 0.1 CPU core (millicores). CPU limits throttle the process — it does not get killed.

**Memory units:** `128Mi` = 128 mebibytes. Memory limits are enforced strictly — exceeding the limit triggers an OOMKill.

### Choosing Appropriate Values

1. **Start with profiling** — measure actual usage under realistic load with `kubectl top pods`
2. **Request ≈ typical usage** — the scheduler uses requests for placement decisions
3. **Limit = 2–4× request** — allows burst headroom without runaway consumption
4. **Go app** uses less memory than Python due to lower runtime overhead → smaller values

---

## Task 4 — HashiCorp Vault Integration

### Installing Vault via Helm

```bash
# Add the HashiCorp Helm repository
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

# Install Vault in dev mode (NOT for production)
helm install vault hashicorp/vault \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true"
```

### Verifying Vault Pods

```bash
kubectl get pods -l app.kubernetes.io/name=vault
```

```
NAME                                    READY   STATUS    RESTARTS   AGE
vault-0                                 1/1     Running   0          2m
vault-agent-injector-xxxxxxxxx-xxxxx    1/1     Running   0          2m
```

### Configuring Vault (KV Secrets Engine)

```bash
# Exec into Vault pod
kubectl exec -it vault-0 -- /bin/sh

# Enable KV v2 secrets engine
vault secrets enable -path=secret kv-v2

# Store secrets for app-python
vault kv put secret/app-python/config \
  secret_key="my-super-secret-key" \
  database_password="prod-db-password-123"

# Store secrets for app-go
vault kv put secret/app-go/config \
  secret_key="go-app-secret-key" \
  database_password="go-db-password-456"

# Verify
vault kv get secret/app-python/config
```

Output:
```
====== Secret Path ======
secret/data/app-python/config

======= Metadata =======
Key              Value
---              -----
created_time     2025-01-01T00:00:00.000000000Z
version          1

====== Data ======
Key                  Value
---                  -----
database_password    prod-db-password-123
secret_key           my-super-secret-key
```

### Configuring Kubernetes Authentication

```bash
# Enable Kubernetes auth method
vault auth enable kubernetes

# Configure it with the cluster's API server address
vault write auth/kubernetes/config \
  kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443"
```

### Creating Policy and Role

```bash
# Create a policy that grants read access to app-python secrets
vault policy write app-python-policy - <<EOF
path "secret/data/app-python/config" {
  capabilities = ["read"]
}
EOF

# Create a role binding the policy to the app-python service account
vault write auth/kubernetes/role/app-python \
  bound_service_account_names=default \
  bound_service_account_namespaces=default \
  policies=app-python-policy \
  ttl=24h

# Same for app-go
vault policy write app-go-policy - <<EOF
path "secret/data/app-go/config" {
  capabilities = ["read"]
}
EOF

vault write auth/kubernetes/role/app-go \
  bound_service_account_names=default \
  bound_service_account_namespaces=default \
  policies=app-go-policy \
  ttl=24h
```

### Enabling Vault Agent Injection

The deployment template includes conditional Vault annotations controlled by `vault.enabled` in `values.yaml`:

```yaml
# values.yaml
vault:
  enabled: true          # set to true to enable injection
  role: "app-python"
  secretPath: "secret/data/app-python/config"
```

When enabled, the rendered deployment contains:

```yaml
spec:
  template:
    metadata:
      annotations:
        vault.hashicorp.com/agent-inject: "true"
        vault.hashicorp.com/role: "app-python"
        vault.hashicorp.com/agent-inject-secret-config: "secret/data/app-python/config"
        vault.hashicorp.com/agent-inject-template-config: |
          {{- with secret "secret/data/app-python/config" -}}
          APP_SECRET_KEY={{ .Data.data.secret_key }}
          APP_DATABASE_PASSWORD={{ .Data.data.database_password }}
          {{- end -}}
```

### Deploy with Vault Enabled

```bash
helm install myrelease k8s/app-python \
  --set vault.enabled=true \
  --set secrets.secretKey="placeholder" \
  --set secrets.databasePassword="placeholder"
```

### Verifying Secret Injection

```bash
# Pod should now have a vault-agent sidecar
kubectl get pod <pod-name> -o jsonpath='{.spec.containers[*].name}'
# Output: app-python vault-agent

# The injected secret file is available at /vault/secrets/config
kubectl exec <pod-name> -c app-python -- cat /vault/secrets/config
# Output:
# APP_SECRET_KEY=my-super-secret-key
# APP_DATABASE_PASSWORD=prod-db-password-123
```

### Sidecar Injection Pattern Explained

Vault Agent injection works via a **mutating admission webhook**:

1. The `vault-agent-injector` pod registers a webhook with the Kubernetes API server
2. When a pod spec with `vault.hashicorp.com/agent-inject: "true"` is submitted, the webhook intercepts it
3. The injector mutates the pod spec, adding an **init container** (fetches secrets before app starts) and a **sidecar container** (keeps secrets fresh via lease renewal)
4. Both containers share a volume mounted at `/vault/secrets/` with the app container
5. Secrets are written as files — templates control the format

```
┌─────────────────────────────────────────────┐
│                     Pod                      │
│                                              │
│  ┌──────────────┐    /vault/secrets/         │
│  │  vault-agent │ ──────────────────────┐   │
│  │  (sidecar)   │                       │   │
│  └──────────────┘                       ▼   │
│         │                      ┌──────────┐ │
│         │ Vault API            │  Shared  │ │
│         ▼                      │  Volume  │ │
│  ┌──────────────┐              └────┬─────┘ │
│  │ HashiCorp    │                   │       │
│  │ Vault Server │            ┌──────▼─────┐ │
│  └──────────────┘            │  app-python │ │
│                              │ (reads file)│ │
│                              └────────────┘ │
└─────────────────────────────────────────────┘
```

---

## Bonus — Vault Agent Templates & Named Templates

### Template Annotation for Custom Format

The `vault.hashicorp.com/agent-inject-template-*` annotation controls how Vault Agent renders the secret file. Our charts use it to write secrets in `.env` key=value format:

```yaml
vault.hashicorp.com/agent-inject-template-config: |
  {{- with secret "secret/data/app-python/config" -}}
  APP_SECRET_KEY={{ .Data.data.secret_key }}
  APP_DATABASE_PASSWORD={{ .Data.data.database_password }}
  {{- end -}}
```

This produces `/vault/secrets/config`:
```
APP_SECRET_KEY=my-super-secret-key
APP_DATABASE_PASSWORD=prod-db-password-123
```

### Dynamic Secret Rotation

Vault Agent handles secret rotation automatically:

- Vault leases have a **TTL** (set to `24h` in our role)
- The Vault Agent sidecar **renews the lease** before expiry
- When a lease cannot be renewed (e.g., the secret was rotated), the agent re-authenticates and re-fetches
- The `vault.hashicorp.com/agent-inject-command` annotation can trigger a signal or script when secrets change:

```yaml
vault.hashicorp.com/agent-inject-command-config: "kill -HUP 1"
```

This sends `SIGHUP` to PID 1 (the app process), which can be used to trigger a graceful config reload.

### Named Templates in `_helpers.tpl` (DRY Principle)

Both charts define a named template for common, non-sensitive environment variables:

**`app-python/templates/_helpers.tpl`:**
```
{{/*
Common environment variables (named template for DRY principle)
*/}}
{{- define "app-python.envVars" -}}
- name: APP_ENV
  value: {{ .Values.environment | default "development" | quote }}
- name: LOG_LEVEL
  value: {{ .Values.logLevel | default "info" | quote }}
{{- end }}
```

**Usage in `deployment.yaml`:**
```yaml
env:
  {{- include "app-python.envVars" . | nindent 12 }}
```

**Benefits:**
- **DRY:** Environment variable definitions live in one place
- **Reusable:** Any template (Deployment, Job, CronJob) can `include` it
- **Consistent:** Changing a variable name updates all consumers at once
- **Testable:** `helm template` renders the named template output for inspection

---

## Security Analysis — K8s Secrets vs Vault

### Comparison

| Feature                        | Kubernetes Secrets          | HashiCorp Vault                     |
|--------------------------------|-----------------------------|-------------------------------------|
| Storage                        | etcd (base64, opt-in encrypt) | Encrypted storage backend          |
| Encryption at rest             | Opt-in (`EncryptionConfig`) | Always on                           |
| Access control                 | RBAC (coarse-grained)       | Fine-grained policies per path      |
| Secret rotation                | Manual (re-apply manifest)  | Dynamic secrets + auto-rotation     |
| Audit logging                  | K8s audit log               | Dedicated audit log per operation   |
| Dynamic secrets                | ❌ No                       | ✅ Yes (DB, PKI, AWS, etc.)         |
| Leases / TTL                   | ❌ No                       | ✅ Yes                              |
| Multi-cluster / multi-cloud    | ❌ Per-cluster              | ✅ Central secret store             |
| Operational complexity         | Low                         | Medium-High                         |
| GitOps-friendly                | ⚠️ Only with Sealed Secrets | ✅ Reference by path, not value     |

### When to Use Kubernetes Secrets

- Simple applications with few secrets
- Development and staging environments
- When etcd encryption + RBAC is sufficient
- When team size and audit requirements are low
- When operational simplicity outweighs security sophistication

### When to Use HashiCorp Vault

- Production workloads with strict compliance requirements (PCI-DSS, SOC 2, HIPAA)
- Dynamic secrets needed (short-lived DB credentials, X.509 certificates)
- Multiple clusters or cloud providers sharing a common secret store
- Detailed audit trails required per secret access
- Secret rotation without application restarts
- Large teams where fine-grained access control matters

### Production Recommendations

1. **Never store real secrets in Git** — use `--set` flags, Sealed Secrets, or Vault
2. **Enable etcd encryption at rest** if using K8s Secrets in production
3. **Use Vault in production** for any sensitive workload; K8s Secrets for dev/CI
4. **Apply least-privilege RBAC** — no service account should have `list secrets` in production
5. **Rotate secrets regularly** — Vault automates this; K8s Secrets require manual rotation
6. **Use `stringData` in Helm charts** — avoids base64 in values files
7. **Never log secret values** — ensure application code does not print env vars to stdout