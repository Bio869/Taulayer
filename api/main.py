# api/main.py

import logging
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict

from supabase import create_client, Client
from fastapi.responses import JSONResponse
from config import settings
from auth import get_current_user
from routes.workflow_requests import router as requests_router

# configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---- Helpers ----

def get_supabase() -> Client:
    return create_client(settings.supabase_url, settings.supabase_key)

def get_db(current_user: Optional[Dict] = Depends(get_current_user)) -> Client:
    try:
        return get_supabase()
    except Exception as e:
        logger.error(f"DB connection failed: {e}")
        raise HTTPException(503, "Database connection failed")

# ---- App setup ----

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Routes ----

app.include_router(requests_router, prefix="/api")

# ---- Healthcheck and Monitoring ----

@app.get("/healthcheck", tags=["Monitoring"])
async def healthcheck():
    return JSONResponse(status_code=200, content={"status": "ok"})

# ---- Smoke-test endpoints ----

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
async def health(supabase: Client = Depends(get_db)):
    # a trivial DB call to prove connectivity
    try:
        _ = supabase.table("users").select("id").limit(1).execute()
        return {"status": "healthy", "database": "connected", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.debug)
