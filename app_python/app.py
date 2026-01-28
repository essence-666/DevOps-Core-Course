from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from core.config import SERVICE_NAME, SERVICE_VERSION, SERVICE_DESCRIPTION, HOST, PORT
from core.logging import setup_logging
from api.routes import root, health

logger = setup_logging()

app = FastAPI(
    title=SERVICE_NAME,
    version=SERVICE_VERSION,
    description=SERVICE_DESCRIPTION,
)

app.include_router(root.router)
app.include_router(health.router)

@app.exception_handler(404)
async def not_found(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Not Found", "message": "Endpoint does not exist"},
    )

@app.exception_handler(Exception)
async def internal_error(request: Request, exc):
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "message": "An unexpected error occurred"},
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host=HOST, port=PORT)
