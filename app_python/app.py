from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
import time

from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from core.config import SERVICE_NAME, SERVICE_VERSION, SERVICE_DESCRIPTION, HOST, PORT
from core.logging import setup_logging
from core.metrics import (
    http_requests_total,
    http_request_duration_seconds,
    http_requests_in_progress,
)
from api.routes import root, health

logger = setup_logging()

app = FastAPI(
    title=SERVICE_NAME,
    version=SERVICE_VERSION,
    description=SERVICE_DESCRIPTION,
)

# Add request logging and metrics middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    endpoint = request.url.path

    # Skip metrics endpoint from instrumentation to avoid noise
    track = endpoint != "/metrics"

    if track:
        http_requests_in_progress.inc()

    # Log the incoming request
    logger.info(
        "Incoming request",
        extra={
            "method": request.method,
            "path": endpoint,
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent"),
        }
    )

    response = await call_next(request)

    process_time = time.time() - start_time
    log_extra = {
        "method": request.method,
        "path": endpoint,
        "status_code": response.status_code,
        "process_time_ms": round(process_time * 1000, 2),
        "client_ip": request.client.host,
    }

    if track:
        http_requests_in_progress.dec()
        http_requests_total.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=str(response.status_code),
        ).inc()
        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=endpoint,
        ).observe(process_time)

    if response.status_code >= 500:
        logger.error("Request failed with server error", extra=log_extra)
    elif response.status_code >= 400:
        logger.warning("Request failed with client error", extra=log_extra)
    else:
        logger.info("Request completed", extra=log_extra)

    return response


@app.get("/metrics", include_in_schema=False)
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

app.include_router(root.router)
app.include_router(health.router)

@app.exception_handler(404)
async def not_found(request: Request, exc):
    logger.warning(
        "Route not found",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host,
        }
    )
    return JSONResponse(
        status_code=404,
        content={"error": "Not Found", "message": "Endpoint does not exist"},
    )

@app.exception_handler(Exception)
async def internal_error(request: Request, exc):
    logger.exception(
        "Unhandled exception",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host,
        }
    )
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "message": "An unexpected error occurred"},
    )

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting devops-info-service")
    uvicorn.run("app:app", host=HOST, port=PORT)
