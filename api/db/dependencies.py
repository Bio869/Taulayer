# api/db/dependencies.py
from typing import Optional, Dict
from fastapi import Depends, HTTPException
from supabase import create_client, Client
from config import settings
from auth import get_current_user
from services import logger  # if you use logging

def get_supabase() -> Client:
    return create_client(settings.supabase_url, settings.supabase_key)

def get_db(current_user: Optional[Dict] = Depends(get_current_user)) -> Client:
    try:
        return get_supabase()
    except Exception as e:
        logger.error(f"DB connection failed: {e}")
        raise HTTPException(503, "Database connection failed")
