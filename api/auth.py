# api/auth.py

from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from supabase import Client
import hashlib
import secrets
from typing import Optional, Dict, List, Tuple, Any
import logging
import uuid

from db.dependencies import get_db
# helpers for lookups / upserts
from services.request_handler import get_user_by_id, upsert_user_by_external_id

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# (Optional legacy helper; not used by resolve_user_identity anymore)
def get_or_create_anonymous_user(supabase: Client) -> Dict:
    """
    DEPRECATED in the auth-required flow.
    Creates a unique anonymous user (not used by resolve_user_identity).
    """
    anon_pid = f"anonymous_{uuid.uuid4().hex[:8]}"

    supabase.table("users").insert({
        "type": "other",              # enum: 'user prompt' | 'agent prompt' | 'other'
        "default_priority": "low",
        "provided_user_id": anon_pid,
        "api_key_hash": None,
    }).execute()

    created = (
        supabase.table("users")
        .select("id, default_priority")
        .eq("provided_user_id", anon_pid)
        .single()
        .execute()
    )
    return created.data


def resolve_user_identity(
    supabase: Client,
    request: Any,  # expects attrs: user_id (UUID|None), metadata (dict|None)
    current_user: Optional[Dict],
    x_provided_user_id: Optional[str] = None,
) -> Tuple[Dict, List[str]]:
    """
    Resolve the caller's identity by strict precedence (no anonymous fallback):
      1) provided_user_id (header > body)  → upsert/reuse by external ID
      2) internal user_id (payload)        → lookup by UUID (must exist)
      3) API-key user                      → get_current_user()
      4) otherwise                         → 401 Unauthorized

    Returns:
      (user_row: dict, resolution_notes: list[str])

    Raises:
      HTTPException 404 if user_id is supplied but not found.
      HTTPException 401 if no valid identity is provided.
    """
    notes: List[str] = []

    # 1) External ID (header wins, else body metadata)
    provided_id = x_provided_user_id or ((getattr(request, "metadata", None) or {}).get("provided_user_id"))
    if provided_id:
        row = upsert_user_by_external_id(
            supabase,
            provided_id,
            default_priority="medium",
            user_type="other",
        )
        notes.append(f"Resolved via provided_user_id='{provided_id}' (created or reused).")
        return row, notes

    # 2) Internal UUID (for internal tools/tests)
    req_user_id = getattr(request, "user_id", None)
    if req_user_id:
        row = get_user_by_id(supabase, req_user_id)
        if row:
            notes.append(f"Resolved via internal user_id={req_user_id}.")
            return row, notes
        # user_id explicitly provided but not found → 404
        raise HTTPException(status_code=404, detail=f"user_id '{req_user_id}' not found")

    # 3) API-key authenticated user
    if current_user:
        notes.append("Resolved via API-key authentication.")
        return current_user, notes

    # 4) No identity → reject
    raise HTTPException(
        status_code=401,
        detail="Authentication required: provide X-Provided-User-Id, user_id, or a valid X-API-Key.",
    )


def generate_api_key() -> str:
    """Generate a secure API key for a new user or external client."""
    return f"tl_{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    """Securely hash API keys before storing in DB (one-way SHA-256)."""
    return hashlib.sha256(api_key.encode()).hexdigest()


async def get_current_user(
    api_key: Optional[str] = Security(api_key_header),
    supabase: Client = Depends(get_db),
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
            .select("*")
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
