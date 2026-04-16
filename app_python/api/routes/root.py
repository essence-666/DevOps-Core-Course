import time
from datetime import datetime, timezone

from core.config import (
    FRAMEWORK,
    SERVICE_DESCRIPTION,
    SERVICE_NAME,
    SERVICE_VERSION,
)
from core.metrics import endpoint_calls, system_info_duration
from fastapi import APIRouter, HTTPException, Request
from services.runtime import get_uptime
from services.system import get_system_info
from services.visits import increment_visits

router = APIRouter()


@router.get("/")
async def root(request: Request):
    endpoint_calls.labels(endpoint="/").inc()
    visits = increment_visits()
    uptime_seconds, uptime_human = get_uptime()

    t0 = time.time()
    sys_info = get_system_info()
    system_info_duration.observe(time.time() - t0)

    return {
        "service": {
            "name": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "description": SERVICE_DESCRIPTION,
            "framework": FRAMEWORK,
        },
        "system": sys_info,
        "runtime": {
            "uptime_seconds": uptime_seconds,
            "uptime_human": uptime_human,
            "current_time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC",
        },
        "request": {
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent"),
            "method": request.method,
            "path": request.url.path,
        },
        "visits": visits,
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/visits", "method": "GET", "description": "Visit counter"},
            {
                "path": "/error",
                "method": "GET",
                "description": "Test endpoint that returns 500 error",
            },
        ],
    }


@router.get("/error")
async def error_test():
    """Test endpoint that returns a 500 error for testing error logging"""
    endpoint_calls.labels(endpoint="/error").inc()
    raise HTTPException(
        status_code=500, detail="Internal Server Error - Test endpoint triggered"
    )
