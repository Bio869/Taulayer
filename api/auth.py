from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from supabase import Client
import hashlib
import secrets
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# API Key header configuration
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def generate_api_key() -> str:
    """Generate a secure API key"""
    return f"tl_{secrets.token_urlsafe(32)}"

def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()

async def get_current_user(
    api_key: Optional[str] = Security(api_key_header),
    supabase: Client = Depends(lambda: None)  # Will be injected
):
    """Validate API key and return user data"""
    if not api_key:
        # Allow public access for now, return None
        return None
    
    # Hash the provided API key
    api_key_hash = hash_api_key(api_key)
    
    try:
        # Look up user by API key hash
        result = supabase.table("users").select("*").eq("api_key_hash", api_key_hash).single().execute()
        
        if result.data:
            return result.data
        else:
            raise HTTPException(
                status_code=403,
                detail="Invalid API key"
            )
    except Exception as e:
        logger.error(f"Auth error: {str(e)}")
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )

async def require_api_key(
    current_user = Depends(get_current_user)
):
    """Require valid API key for protected endpoints"""
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="API key required"
        )
    return current_user