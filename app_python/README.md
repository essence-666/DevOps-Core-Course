# DevOps Info Service (FastAPI)

## Overview

DevOps Info Service is a FastAPI-based web application that provides detailed
information about the service itself, system environment, runtime status, and
incoming HTTP requests.

---

## Prerequisites

- Python 3.11+
- pip

---

## Installation

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
````

---

## Running the Application

```bash
python app.py
```

### Custom Configuration

```bash
PORT=8080 python app.py
HOST=127.0.0.1 PORT=3000 python app.py
```

---

## API Endpoints

| Method | Path    | Description                    |
| ------ | ------- | ------------------------------ |
| GET    | /       | Service and system information |
| GET    | /health | Health check                   |

---

## Configuration

| Variable | Default | Description      |
| -------- | ------- | ---------------- |
| HOST     | 0.0.0.0 | Bind address     |
| PORT     | 5000    | Application port |
| DEBUG    | False   | Debug mode       |

```


Окей, добавляем ровно то, **что от тебя хотят по лабе**, без воды и с объяснениями. Ниже — **готовый Docker-раздел**, который ты просто **вставляешь в `README.md`** (обычно после `Running the Application`).

---

## Docker

This application can be run inside a Docker container.
The Docker image is built following Docker best practices: minimal base image, non-root user, optimized layer caching, and a clean build context.

### Dockerfile Overview

The Dockerfile is designed for production usage and includes the following decisions:

* **Base image**: `python:3.13-slim`
  Chosen for a balance between small image size and good compatibility with Python packages.

* **Non-root user**:
  The application runs as a dedicated non-root user to reduce security risks.

* **Optimized layer caching**:
  Dependencies are installed before copying application code, allowing Docker to reuse cached layers when only source code changes.

* **Minimal file copy**:
  Only required source files are copied into the image to keep it small and clean.

* **`.dockerignore` usage**:
  Excludes development artifacts, virtual environments, VCS files, and caches to reduce build context size and improve build performance.

---

### Build the Docker Image

```bash
docker build -t devops-info-service .
```

---

### Run the Container

```bash
docker run -p 8000:8000 devops-info-service
```

The application will be available at:

```
http://localhost:8000
```

---

### Environment Variables in Docker

You can override configuration values using environment variables:

```bash
docker run -p 8000:8000 \
  -e HOST=0.0.0.0 \
  -e PORT=8000 \
  devops-info-service
```

## Visit Counter

The service tracks the number of visits to the root endpoint (`/`). The counter is persisted to a file so it survives container restarts.

### Endpoints

| Endpoint  | Method | Description                          |
|-----------|--------|--------------------------------------|
| `/`       | GET    | Service info (increments visit count) |
| `/visits` | GET    | Returns current visit count          |

### Configuration

| Environment Variable | Default         | Description                     |
|----------------------|-----------------|---------------------------------|
| `VISITS_FILE`        | `/data/visits`  | Path to the visit counter file  |

### Local Testing with Docker Compose

```bash
# Start the service
docker compose up -d

# Access root endpoint a few times (increments counter)
curl http://localhost:8000/
curl http://localhost:8000/
curl http://localhost:8000/

# Check visit count
curl http://localhost:8000/visits
# {"visits": 3}

# Restart container — counter persists
docker compose restart
curl http://localhost:8000/visits
# {"visits": 3}

# Stop and remove containers (volume persists)
docker compose down
docker compose up -d
curl http://localhost:8000/visits
# {"visits": 3}
```
