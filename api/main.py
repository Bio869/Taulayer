# api/main.py

import logging
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from supabase import Client

from config import settings
from db.dependencies import get_supabase
from routes.workflow_requests import router as requests_router
from fastapi.exceptions import RequestValidationError

# configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---- App setup ----
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=getattr(settings, "api_description", None),
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=getattr(settings, "cors_origins", ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Global Exception Handling ----
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Ensure API consistently returns a clean JSON error for unauthorized/unverified users.
    """
    logger.warning(f"HTTP {exc.status_code} - {exc.detail} - Path: {request.url}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status": "error"}
    )

# ---- Routes ----
app.include_router(requests_router, prefix="/api")

# ---- Healthcheck and Monitoring ----
@app.get("/healthcheck", tags=["Monitoring"])
async def healthcheck():
    return JSONResponse(status_code=200, content={"status": "ok"})

@app.get("/ping")
async def ping():
    return {"pong": True}

@app.get("/")
async def root():
    return {
        "message": "Welcome to Taulayer AI Optimization API",
        "version": settings.api_version,
    }

@app.get("/health")
async def health(supabase: Client = Depends(get_supabase)):
    try:
        _ = supabase.table("users").select("id").limit(1).execute()
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error at {request.url}: {exc}")
    return JSONResponse(status_code=500, content={"error": "Internal server error", "status": "error"})

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"HTTP 422 - Validation error - Path: {request.url} - {exc.errors()}")
    return JSONResponse(status_code=422, content={"error": "Invalid request payload", "status": "error"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=getattr(settings, "debug", False))
