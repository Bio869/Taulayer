# api/auth.py

from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from supabase import Client
import hashlib
import secrets
from typing import Optional, Dict, List, Tuple, Any
import logging
from db.dependencies import get_supabase
from services.request_handler import get_user_by_id, get_user_by_external_id

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def resolve_user_identity(
    supabase: Client,
    request: Any,  # expects attrs: user_id (UUID|None), metadata (dict|None)
    current_user: Optional[Dict],
    x_provided_user_id: Optional[str] = None,
) -> Tuple[Dict, List[str]]:
    """
    Resolve the caller's identity by strict precedence:
      1) provided_user_id (header > body)  → lookup only (must exist)
      2) internal user_id (payload)        → lookup by UUID (must exist)
      3) API-key user                      → get_current_user()
      4) otherwise                         → 401 Unauthorized

    Only verified users reach the caller.
    """
    notes: List[str] = []

    # 1) External ID lookup
    provided_id = x_provided_user_id or ((getattr(request, "metadata", None) or {}).get("provided_user_id"))
    if provided_id:
        row = get_user_by_external_id(supabase, provided_id)
        if not row:
            logger.warning(f"Unverified provided_user_id: {provided_id}")
            raise HTTPException(status_code=404, detail="User not found")
        logger.info(f"Resolved user via provided_user_id='{provided_id}' → {row['id']}")
        notes.append(f"Resolved via provided_user_id='{provided_id}'.")
        return row, notes

    # 2) Internal UUID lookup
    req_user_id = getattr(request, "user_id", None)
    if req_user_id:
        try:
            row = get_user_by_id(supabase, req_user_id)
        except HTTPException:
            # already normalized (e.g., 503 from the helper)
            raise
        except Exception as e:
            logger.error(f"Lookup error for internal user_id={req_user_id}: {e}")
            raise HTTPException(status_code=503, detail="Service temporarily unavailable: user lookup failed.")

        if not row:
            logger.warning(f"Unverified internal user_id: {req_user_id}")
            raise HTTPException(status_code=404, detail="User not found")

        notes.append(f"Resolved via internal user_id={req_user_id}.")
        return row, notes

    # 3) API-key authenticated user
    if current_user:
        notes.append("Resolved via API-key authentication.")
        return current_user, notes

    # 4) No valid identity
    logger.warning("Unauthenticated request with no valid identity")
    raise HTTPException(
        status_code=401,
        detail="Authentication required: provide X-Provided-User-Id, user_id, or a valid X-API-Key."
    )


def generate_api_key() -> str:
    """Generate a secure API key for a new user or external client."""
    return f"tl_{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    """Securely hash API keys before storing in DB (one-way SHA-256)."""
    return hashlib.sha256(api_key.encode()).hexdigest()


async def get_current_user(
    api_key: Optional[str] = Security(api_key_header),
    supabase: Client = Depends(get_supabase),
):
    """
    Resolve current user by API key. If no API key is provided, return None (unauthenticated).
    """
    if not api_key:
        return None

    api_key_hash = hash_api_key(api_key)
    try:
        result = (
            supabase.table("users")
            .select("id, default_priority, provided_user_id, type")
            .eq("api_key_hash", api_key_hash)
            .single()
            .execute()
        )
        if result.data:
            return result.data
        raise HTTPException(status_code=403, detail="Invalid API key")
    except Exception as e:
        logger.error(f"Auth error: {str(e)}")
        raise HTTPException(status_code=403, detail="Invalid API key")


async def require_api_key(current_user=Depends(get_current_user)):
    """Guard for endpoints that must require a valid API key."""
    if not current_user:
        raise HTTPException(status_code=401, detail="API key required")
    return current_user