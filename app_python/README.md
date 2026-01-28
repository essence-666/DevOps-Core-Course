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
