# api/auth.py

from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from supabase import Client
import hashlib
import secrets
from typing import Optional
import logging
import uuid

# API Key header configuration: expects `X-API-Key` in headers
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Create a logger object for this module (file)
# __name__ ensures the logger name matches the module's name (e.g., 'auth')
logger = logging.getLogger(__name__)

# Sets up logging to show messages at INFO level or higher in the console. Can be customized for format or file output.
logging.basicConfig(level=logging.INFO)

# create anonymous user if needed
def get_or_create_anonymous_user(supabase: Client):
    anon_id = str(uuid.uuid4())

    # Optional: insert anonymous user into `users` table if needed
    supabase.table("users").insert({
        "id": anon_id,
        "type": "other",
        "default_priority": "low",
        "provided_user_id": f"anonymous_{anon_id[:8]}",
        "api_key_hash": None  
    }).execute()

    return {"id": anon_id, "type": "anonymous"}

def generate_api_key() -> str:
    """Generate a secure API key for a new user or external client.
    Example: tl_XYZ...123"""
    return f"tl_{secrets.token_urlsafe(32)}"

def hash_api_key(api_key: str) -> str:
    """Securely hash API keys before storing in DB (one-way SHA-256)."""
    return hashlib.sha256(api_key.encode()).hexdigest()

async def get_current_user(
    api_key: Optional[str] = Security(api_key_header),
    supabase: Client = Depends(lambda: None)
):
    """Main auth resolver.
    - If no API key: treat as anonymous (returns None)
    - If API key present: hash it and match to user by `api_key_hash` in Supabase
    """
    if not api_key:
        return None  # Optional: fallback to anonymous usage

    api_key_hash = hash_api_key(api_key)

    try:
        result = supabase.table("users").select("*").eq("api_key_hash", api_key_hash).single().execute()
        if result.data:
            return result.data  # Optionally wrap in UserSchema later
        else:
            raise HTTPException(status_code=403, detail="Invalid API key")
    except Exception as e:
        logger.error(f"Auth error: {str(e)}")
        raise HTTPException(status_code=403, detail="Invalid API key")

# Protect any endpoint with Depends(require_api_key)
async def require_api_key(current_user = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="API key required")
    return current_user
