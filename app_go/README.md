# DevOps Info Service (Go)

## Overview

DevOps Info Service is a Go-based web application that provides detailed
information about the service itself, system environment, runtime status, and
incoming HTTP requests.

The application is implemented in a single source file for simplicity.

---

## Prerequisites

- Go 1.22+
- Docker (optional)

---

## Running Locally

```bash
go run main.go
````

### Custom Configuration

```bash
PORT=8080 go run main.go
HOST=127.0.0.1 PORT=3000 go run main.go
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

---

## Docker Build (Multi-Stage)

```bash
docker build -t devops-info-go .
docker run -p 5000:5000 devops-info-go
```
