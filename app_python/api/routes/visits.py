from fastapi import APIRouter
from services.visits import get_visits

router = APIRouter()


@router.get("/visits")
async def visits():
    """Return current visit count."""
    return {"visits": get_visits()}
