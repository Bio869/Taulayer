# api/auth.py
from __future__ import annotations

import hashlib
import logging
import secrets
from typing import Optional, Dict, List, Tuple, Any, TypedDict

import jwt
from fastapi import HTTPException, Security, Depends, Request, status
from fastapi.security import APIKeyHeader
from supabase import Client

from config import settings
from db.dependencies import get_supabase
from services.db_guard import with_retry
from services.request_handler import get_user_by_id, get_user_by_external_id

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ------------------------- API key helpers (unchanged) -------------------------

def generate_api_key() -> str:
    return f"tl_{secrets.token_urlsafe(32)}"

def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()

async def get_current_user(
    api_key: Optional[str] = Security(api_key_header),
    supabase: Client = Depends(get_supabase),
):
    if not api_key:
        return None
    api_key_hash = hash_api_key(api_key)
    try:
        result = with_retry(lambda:
            supabase.table("users")
            .select("id, default_priority, provided_user_id, type, client_id")
            .eq("api_key_hash", api_key_hash)
            .single()
            .execute()
        )
        if result.data:
            return result.data
        raise HTTPException(status_code=403, detail="Invalid API key")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth error: {str(e)}")
        raise HTTPException(status_code=503, detail="Auth unavailable")

async def require_api_key(current_user=Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="API key required")
    return current_user

# ------------------------- Supabase JWT (unchanged) ---------------------------

class Identity(TypedDict, total=False):
    user_id: Optional[str]
    email: Optional[str]

JWKS_URL = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
_JWK_CLIENT = jwt.PyJWKClient(JWKS_URL)  # cache client

#_JWKS: dict | None = None

# async def _get_jwks() -> dict:
#     global _JWKS
#     if _JWKS:
#         return _JWKS
#     jwks_url = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
#     async with httpx.AsyncClient(timeout=5) as c:
#         r = await c.get(jwks_url)
#         r.raise_for_status()
#         _JWKS = r.json()
#         return _JWKS

async def get_identity(request: Request) -> Identity:
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = auth.split(" ", 1)[1].strip()

    # Decide by token header alg
    try:
        header = jwt.get_unverified_header(token)
        alg = (header.get("alg") or "").upper()
        unverified = jwt.decode(token, options={"verify_signature": False})
        logger.info(f"JWT header alg={alg}, iss={unverified.get('iss')}, sub={unverified.get('sub')}, email={unverified.get('email')}")
        logger.info(f"JWT verification path: {'RS256' if alg=='RS256' else 'HS256'}")
    except Exception:
        alg = ""
    # Print the token header and the chosen path
    logger.info(f"JWT header alg={alg}, using {'RS256' if alg == 'RS256' else 'HS256'} path")

# 1) Try RS256 via JWKS
    try:
        if alg and alg != "RS256":
            raise Exception("skip_rs256")  # jump to HS256
        signing_key = _JWK_CLIENT.get_signing_key_from_jwt(token).key
        claims = jwt.decode(
            token,
            key=signing_key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        logger.info("JWT verified using RS256 / JWKS")
    except Exception as e_rs:
        # 2) Fallback to HS256 (Supabase default)
        hs_secret = settings.supabase_jwt_secret or settings.supabase_key or settings.supabase_service_key
        claims = jwt.decode(token, key=hs_secret, algorithms=["HS256"], options={"verify_aud": False})
        logger.info("JWT verified using HS256 / project JWT secret")
        if not hs_secret:
            logger.error("JWT verification failed via RS256 and no HS256 secret configured")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: JWKS empty and no HS256 secret configured",
            )
        try:
            claims = jwt.decode(
                token,
                key=hs_secret,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
            logger.info("JWT verified using HS256 / project secret")
        except Exception as e_hs:
            logger.error(f"JWT verification failed via HS256: {e_hs}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e_hs}")
    uid = claims.get("sub")
    email = claims.get("email")
    if not (uid or email):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    return Identity(user_id=uid, email=email)

# ------------------------- NEW: optional JWT helper ---------------------------

async def maybe_get_identity(request: Request) -> Optional[Identity]:
    """
    Return Identity when Authorization: Bearer is present; otherwise None.
    Still uses the same verifier, so invalid tokens -> 401.
    """
    auth = request.headers.get("authorization", "")
    if not auth or not auth.lower().startswith("bearer "):
        return None
    return await get_identity(request)

# ------------------------- identity precedence (keep one) ---------------------

def resolve_user_identity(
    supabase: Client,
    request: Any,                    # expects attrs: user_id, metadata
    current_user: Optional[Dict],
    x_provided_user_id: Optional[str] = None,
) -> Tuple[Dict, List[str]]:
    notes: List[str] = []
    # 1) External ID: header > body.metadata.provided_user_id
    provided_id = x_provided_user_id or ((getattr(request, "metadata", None) or {}).get("provided_user_id"))
    if provided_id:
        row = get_user_by_external_id(supabase, provided_id)
        if not row:
            logger.warning(f"Unverified provided_user_id: {provided_id}")
            raise HTTPException(status_code=404, detail="User not found")
        notes.append("Logged in using external ID")
        return row, notes
    # 2) Internal UUID
    req_user_id = getattr(request, "user_id", None)
    if req_user_id:
        try:
            row = get_user_by_id(supabase, req_user_id)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Lookup error for internal user_id={req_user_id}: {e}")
            raise HTTPException(status_code=503, detail="Service temporarily unavailable: user lookup failed.")
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        notes.append("Logged in using internal ID")
        return row, notes
    # 3) API-key user
    if current_user:
        notes.append("Logged in using API-key authentication")
        return current_user, notes
    # 4) None
    raise HTTPException(
        status_code=401,
        detail="Authentication required: provide X-Provided-User-Id, user_id, or a valid X-API-Key.",
    )
