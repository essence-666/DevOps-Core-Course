from fastapi import APIRouter
from datetime import datetime, timezone
from services.runtime import get_uptime

router = APIRouter()

@router.get("/health")
async def health():
    uptime_seconds, _ = get_uptime()

    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime_seconds,
    }
