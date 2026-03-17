принял, делаем **сухо, академично, без воды**, чтобы ассистенту было **нечего резать**.
Ниже **чистый `.md` код**, копипастой.

---

## 📄 `app_python/docs/LAB01.md`

````md
# Lab 01 – DevOps Info Service

## Framework Selection

### Chosen Framework: FastAPI

FastAPI was selected for this laboratory work due to its high performance,
native support for ASGI, automatic OpenAPI documentation, and clean modular
architecture support. These features align well with DevOps requirements such
as observability, scalability, and maintainability.

FastAPI also allows easy extension of the application in future labs without
rewriting core components.

### Comparison with Alternatives

| Framework | Pros | Cons | Reason Not Chosen |
|---------|------|------|-------------------|
| FastAPI | High performance, async support, OpenAPI, type hints | Slightly higher learning curve | Chosen |
| Flask | Simple, lightweight | No async by default, manual validation | Limited scalability |
| Django | Full-featured, ORM, admin panel | Heavyweight, overkill for microservice | Excess complexity |

---

## Best Practices Applied

### 1. Modular Project Structure

The application is split into logical modules:
- `core` – configuration and logging
- `api` – HTTP routes
- `services` – business logic

**Example:**
```python
app.include_router(root.router)
app.include_router(health.router)
````

**Importance:**
Improves readability, scalability, and maintainability of the codebase.

---

### 2. Environment-Based Configuration

Configuration values are read from environment variables.

**Example:**

```python
PORT = int(os.getenv("PORT", 5000))
```

**Importance:**
Allows easy configuration changes without modifying source code, following
the Twelve-Factor App methodology.

---

### 3. Centralized Logging

A unified logging setup is used across the application.

**Example:**

```python
logger = setup_logging()
```

**Importance:**
Simplifies debugging and is essential for production monitoring.

---

### 4. Health Check Endpoint

A dedicated `/health` endpoint is implemented.

**Example:**

```python
@router.get("/health")
async def health_check():
    return {"status": "healthy"}
```

**Importance:**
Required for container orchestration systems and service monitoring.

---

### 5. Explicit Error Handling

Custom handlers for 404 and 500 errors are defined.

**Example:**

```python
@app.exception_handler(404)
async def not_found(request: Request, exc):
```

**Importance:**
Provides consistent error responses and improves API reliability.

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
    "version": "1.0.0"
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
  "status": "healthy",
  "uptime_seconds": 120
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

### Problem 1: ASGI application import error

**Issue:**
Uvicorn could not import the application module when using a modular structure.

**Solution:**
Corrected the `uvicorn.run()` module reference to match the entrypoint file.

---

### Problem 2: Growing complexity of a single file

**Issue:**
Maintaining all logic in a single file would not scale for future labs.

**Solution:**
Refactored the application into multiple modules with clear responsibility
boundaries.

````

