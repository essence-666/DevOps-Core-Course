from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import time

from core.config import SERVICE_NAME, SERVICE_VERSION, SERVICE_DESCRIPTION, HOST, PORT
from core.logging import setup_logging
from api.routes import root, health

logger = setup_logging()

app = FastAPI(
    title=SERVICE_NAME,
    version=SERVICE_VERSION,
    description=SERVICE_DESCRIPTION,
)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log the incoming request
    logger.info(
        "Incoming request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent"),
        }
    )
    
    response = await call_next(request)
    
    # Log the response with appropriate level based on status code
    process_time = time.time() - start_time
    log_extra = {
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "process_time_ms": round(process_time * 1000, 2),
        "client_ip": request.client.host,
    }
    
    if response.status_code >= 500:
        logger.error("Request failed with server error", extra=log_extra)
    elif response.status_code >= 400:
        logger.warning("Request failed with client error", extra=log_extra)
    else:
        logger.info("Request completed", extra=log_extra)
    
    return response

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
