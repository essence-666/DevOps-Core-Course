# LAB03 – CI/CD, Testing & Security for FastAPI Application

## Overview

This project demonstrates implementation of a CI pipeline for a Python FastAPI application including:

* Code linting
* Unit testing
* Static security analysis
* Dependency vulnerability scanning
* Docker image build validation

The goal of this lab is to build a reliable and automated CI workflow following DevOps best practices.

---

# Application Description

The application is built using **FastAPI** and provides:

* `GET /` — root endpoint
* `GET /health` — health check endpoint
* Error handling routes

Testing is performed using:

* `pytest`
* `fastapi.testclient`

---

# Testing

Unit tests are located in:

```
app_python/tests/
```

Run locally:

```bash
pytest
```

All tests must pass for CI to succeed.

---

# Linting

We use **Ruff** for linting.

Run locally:

```bash
ruff check .
```

Linting ensures:

* PEP8 compliance
* Clean imports
* No unused variables
* No obvious code issues

CI fails if linting errors are found.

---

# Security Scanning

## 1️Static Code Analysis – Bandit

Instead of Snyk, **Bandit** was used.

### Why not Snyk?

Snyk requires an API token configured in repository secrets. Due to token validation issues in CI, it was not possible to fully automate Snyk integration.

To maintain a fully automated pipeline, Bandit was selected.

### Why Bandit?

* Open-source
* No authentication required
* Designed for Python
* CI-friendly
* Maintained by OpenStack Security Team

Bandit scans for:

* Insecure function usage (`eval`, `exec`)
* Weak cryptography
* Unsafe subprocess calls
* Hardcoded credentials
* Insecure random usage

Run locally:

```bash
bandit -r app_python
```

CI fails if high severity issues are detected.

---

## Dependency Vulnerability Scanning – pip-audit

We use:

```bash
pip-audit
```

It checks Python dependencies for known CVEs.

If vulnerabilities are found, CI fails.

---

# Docker

The project includes a Dockerfile.

Build locally:

```bash
docker build -t fastapi-app .
```

Run:

```bash
docker run -p 5000:5000 fastapi-app
```

The application will be available at:

```
http://localhost:5000
```

---

# CI Pipeline

GitHub Actions workflow:

```
.github/workflows/ci.yml
```

## CI Stages

### Install dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

---

###  Lint

```bash
ruff check .
```

---

###  Tests

```bash
pytest
```

---

### Security Scan

```bash
bandit -r app_python
pip-audit
```

---

### Docker Build

```bash
docker build -t fastapi-app .
```

---

# CI Guarantees

The pipeline ensures:

* Code quality validation
* Test coverage enforcement
* Security issue detection
* Dependency vulnerability control
* Docker image build validation

If any step fails — the pipeline fails.

---

# Technologies Used

* Python 3.x
* FastAPI
* Pytest
* Ruff
* Bandit
* pip-audit
* Docker
* GitHub Actions

---

# DevOps Best Practices Applied

* Automated testing
* Automated linting
* Automated security scanning
* Fail-fast CI strategy
* Reproducible builds
* Infrastructure-as-Code for CI

---

# Conclusion

This lab demonstrates implementation of a production-like CI pipeline for a Python web application.

The project integrates testing, linting, security scanning, and container validation to ensure code reliability, security, and maintainability.

[The docker images with release by tag 1.0.0 1.0.1 etc](https://hub.docker.com/repository/docker/essence666/devops-info-service/general)
