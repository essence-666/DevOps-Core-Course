# Lab 01 – DevOps Info Service (Go)

## Framework Selection

### Chosen Language and Framework: Go (net/http)

The Go programming language with the standard `net/http` package was chosen
for this laboratory work. Go is widely used in DevOps and cloud-native
environments due to its performance, static compilation, simplicity, and
excellent support for concurrent workloads.

Using the standard library avoids unnecessary dependencies and keeps the
service lightweight and predictable.

### Comparison with Alternatives

| Option | Pros | Cons | Reason Not Chosen |
|------|------|------|-------------------|
| Go (net/http) | Fast, static binary, no dependencies | Less abstraction | Chosen |
| Gin | Simple routing, middleware | External dependency | Not required |
| Echo | High performance | External dependency | Overkill |
| Python (FastAPI) | Rapid development, async | Interpreted, slower startup | Language diversity |

---

## Best Practices Applied

### 1. Minimal Dependency Usage

Only the Go standard library is used.

**Example:**
```go
import "net/http"
````

**Importance:**
Reduces attack surface, simplifies builds, and improves reliability.

---

### 2. Single Responsibility Structure

Although the application is implemented in a single file, logical separation
is maintained through clearly defined functions.

**Example:**

```go
func healthHandler(w http.ResponseWriter, r *http.Request)
```

**Importance:**
Keeps the code readable while remaining suitable for small services.

---

### 3. Environment-Based Configuration

Runtime configuration is handled via environment variables.

**Example:**

```go
port := os.Getenv("PORT")
```

**Importance:**
Allows flexible deployment across environments without code changes.

---

### 4. Structured JSON Responses

All responses are returned in structured JSON format.

**Example:**

```go
json.NewEncoder(w).Encode(response)
```

**Importance:**
Ensures API consistency and ease of integration.

---

### 5. Health Check Endpoint

A dedicated health check endpoint is implemented.

**Example:**

```go
http.HandleFunc("/health", healthHandler)
```

**Importance:**
Required for monitoring systems and container orchestration platforms.

---

## API Documentation

### GET /

**Description:**
Returns service metadata, system information, runtime statistics, and request
details.

**Example Response:**

```json
{
  "service": {
    "name": "devops-info-service",
    "language": "go"
  }
}
```

---

### GET /health

**Description:**
Returns application health status.

**Example Response:**

```json
{
  "status": "healthy"
}
```

---

### Testing Commands

```bash
curl http://localhost:5000/
curl http://localhost:5000/health
```

---

## Testing Evidence

The following screenshots are provided:

* Main endpoint (`/`) showing full JSON response
* Health check endpoint (`/health`)
* Pretty-printed JSON output in terminal

---

## Challenges & Solutions

### Problem 1: Balancing simplicity and structure

**Issue:**
Splitting the application into multiple files was unnecessary for the scope of
the laboratory work.

**Solution:**
Implemented all logic in a single file while preserving logical separation via
functions.

---

### Problem 2: Container image size optimization

**Issue:**
Default Go images produce relatively large containers.

**Solution:**
Implemented a multi-stage Docker build to produce a minimal runtime image.

````
