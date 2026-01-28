from fastapi import APIRouter, Request
from datetime import datetime, timezone

from core.config import (
    SERVICE_NAME,
    SERVICE_VERSION,
    SERVICE_DESCRIPTION,
    FRAMEWORK,
)
from services.system import get_system_info
from services.runtime import get_uptime

router = APIRouter()

@router.get("/")
async def root(request: Request):
    uptime_seconds, uptime_human = get_uptime()

    return {
        "service": {
            "name": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "description": SERVICE_DESCRIPTION,
            "framework": FRAMEWORK,
        },
        "system": get_system_info(),
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
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"},
        ],
    }
