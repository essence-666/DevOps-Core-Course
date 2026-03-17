# LAB02 — Docker Containerization (Python FastAPI)

## Overview

In this lab, the Python FastAPI application from Lab 1 was containerized using Docker following production-ready best practices. The goal was to create a secure, optimized, and reproducible Docker image, publish it to Docker Hub, and document all technical decisions made during the process.

---

## Docker Best Practices Applied

### Non-root User

The container runs the application as a non-root user instead of the default `root` user.

**Why this matters:**

* Containers are not a full security boundary
* Running as root increases the impact of a potential container breakout
* Follows the principle of least privilege

```dockerfile
RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser
...
USER appuser
```

---

### Specific Base Image Version

The image uses a pinned base image:

```dockerfile
FROM python:3.13-slim
```

**Why this matters:**

* Guarantees reproducible builds
* Prevents unexpected breaking changes
* `slim` provides a good balance between size and compatibility

---

### Optimized Layer Caching

Dependencies are installed before application code is copied:

```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

**Why this matters:**

* Docker caches layers
* Dependency installation is reused if only source code changes
* Significantly speeds up rebuilds

---

### Minimal File Copy

Only required application files are copied into the image:

```dockerfile
COPY core ./core
COPY api ./api
COPY services ./services
COPY app.py .
```

**Why this matters:**

* Smaller image size
* Reduced attack surface
* No unnecessary development files included

---

### .dockerignore Usage

A `.dockerignore` file is used to exclude unnecessary files from the build context.

**Excluded files include:**

* Python cache files (`__pycache__`, `*.pyc`)
* Virtual environments (`venv`, `.venv`)
* Git repository files
* IDE configuration files

**Why this matters:**

* Faster build times
* Smaller build context
* Prevents leaking development artifacts into the image

---

## Image Information & Decisions

### Base Image Choice

* **Image:** `python:3.13-slim`
* Chosen for its small size and compatibility with Python dependencies
* Avoids issues commonly found with Alpine-based Python images

### Final Image Size

The final image size is relatively small compared to a full Python image and is suitable for production usage.

Smaller images:

* Pull faster
* Consume less disk space
* Reduce the number of potential vulnerabilities

---

### Layer Structure Explanation

1. Base image
2. Environment variables
3. Non-root user creation
4. Dependency installation
5. Application code copy
6. Switch to non-root user
7. Application startup

This order maximizes cache efficiency and minimizes rebuild time.

---

## Build & Run Process

### Build Image

```bash
docker build -t devops-info-service .
```

### Run Container

```bash
docker run -p 8000:8000 devops-info-service
```

### Test Endpoints

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status": "ok"}
```

---

## Docker Hub

The image was published to Docker Hub and is publicly accessible.

**Repository:**

```
https://hub.docker.com/repository/docker/essence666/app_python_lab_2/general
```

---

## Technical Analysis

### Why the Dockerfile Works This Way

* Dependency layers are cached
* Application runs as non-root
* Minimal runtime environment
* Clear separation between build and runtime concerns

### What Happens If Layer Order Changes

If application code is copied before installing dependencies:

* Any code change invalidates dependency cache
* Dependencies are reinstalled on every build
* Build times increase significantly

---

### Security Considerations

* Application does not run as root
* Smaller image reduces attack surface
* No development tools included
* Environment variables used for configuration

---

### How .dockerignore Improves the Build

* Reduces build context size
* Prevents accidental inclusion of sensitive files
* Improves Docker build performance

---

## Challenges & Solutions

### Challenge: Docker layer cache invalidation

**Solution:**
Copied `requirements.txt` separately before application code.

### Challenge: Running as non-root

**Solution:**
Created a dedicated system user and adjusted file permissions.

---

## What I Learned

* How Docker layer caching works in practice
* Why running containers as non-root is critical
* How to optimize Docker images for production
* How to document containerization decisions clearly

---

## Conclusion

This lab demonstrates a production-ready Docker setup for a Python FastAPI application. By applying best practices such as non-root execution, optimized layer caching, and minimal images, the resulting container is secure, efficient, and suitable for real-world deployment.
