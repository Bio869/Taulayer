# api/services/request_handler.py
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, List, Union, Any
from uuid import UUID

from fastapi import HTTPException
from supabase import Client

from services.logger import log_event
from services.db_guard import with_retry

logger = logging.getLogger(__name__)

# ── Status constants ──────────────────────────────────────────────────────────
STATUS_PENDING = "pending"
STATUS_ANALYZING = "analyzing"
STATUS_EXECUTION = "sent_to_execution"
STATUS_PROCESSING = "processing"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
STATUS_BELOW_THRESHOLD = "below_threshold_suggestions_sent"

# ── Time helpers ──────────────────────────────────────────────────────────────
def _utcnow_iso() -> str:
    """UTC now as ISO-8601 string"""
    return datetime.now(timezone.utc).isoformat()

def _omit_none(d: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy of dict without None values (prevents overwriting with NULLs)."""
    return {k: v for k, v in d.items() if v is not None}

# ──────────────────────────────────────────────────────────────────────────────
# Users
# ──────────────────────────────────────────────────────────────────────────────

def get_user_by_id(supabase: Client, user_id: UUID) -> Optional[Dict]:
    """Fetch a user by internal UUID. Returns a dict or None."""
    res = with_retry(lambda:
        supabase.table("users")
        .select("id, email, client_name, provided_user_id, default_priority")
        .eq("id", str(user_id))
        .limit(1)
        .execute()
    )
    return (res.data or [None])[0]

def get_user_by_external_id(supabase: Client, ext_id: str) -> Optional[Dict]:
    """
    Fetch a user by *provided_user_id* (maps from X-Provided-User-Id).
    (Function name kept for compatibility.)
    """
    res = with_retry(lambda:
        supabase.table("users")
        .select("id, email, client_name, provided_user_id, default_priority")
        .eq("provided_user_id", ext_id)
        .limit(1)
        .execute()
    )
    return (res.data or [None])[0]

def upsert_user_by_external_id(
    supabase: Client,
    ext_id: str,
    default_priority: str = "medium",
    user_type: str = "other",
    email: Optional[str] = None,
) -> Optional[Dict]:
    """
    Upsert a user by *provided_user_id* and return their row.
    (Function name kept for compatibility.)
    """
    row: Dict[str, Any] = {
        "provided_user_id": ext_id,
        "type": user_type,
        "default_priority": default_priority,
    }
    if email:
        row["email"] = email

    with_retry(lambda:
        supabase.table("users").upsert(
            row,
            on_conflict="provided_user_id",
        ).execute()
    )

    res = with_retry(lambda:
        supabase.table("users")
        .select("id, email, client_name, provided_user_id, default_priority")
        .eq("provided_user_id", ext_id)
        .single()
        .execute()
    )
    return res.data if res.data else None

# ──────────────────────────────────────────────────────────────────────────────
# Email-allowlist
# ──────────────────────────────────────────────────────────────────────────────

def get_user_by_email(supabase: Client, email: str) -> Optional[Dict]:
    """Case-insensitive email lookup; existence == allowed."""
    res = with_retry(lambda:
        supabase.table("users")
        .select("id, email, client_name, provided_user_id, default_priority")
        .ilike("email", email)
        .limit(1)
        .execute()
    )
    return (res.data or [None])[0]

def link_provided_user_id_if_missing(supabase: Client, user_id: str, provided_user_id: str) -> None:
    """Attach provided_user_id the first time we see this identity."""
    with_retry(lambda:
        supabase.table("users")
        .update({"provided_user_id": provided_user_id})
        .eq("id", user_id)
        .is_("provided_user_id", None)
        .execute()
    )

def require_known_user_by_email(
    supabase: Client,
    email: Optional[str],
    provided_user_id: Optional[str] = None,
) -> Dict:
    """Allow only if email exists in public.users; do NOT auto-create."""
    if not email:
        raise HTTPException(status_code=401, detail="Missing identity email")

    user = get_user_by_email(supabase, email)
    if not user:
        raise HTTPException(status_code=403, detail="Access not enabled for this email")

    if provided_user_id:
        try:
            link_provided_user_id_if_missing(supabase, user["id"], provided_user_id)
        except Exception:
            logger.debug("Optional provided_user_id link failed for user_id=%s", user["id"])
    return user


# ──────────────────────────────────────────────────────────────────────────────
# Requests
# ──────────────────────────────────────────────────────────────────────────────

def create_request(supabase: Client, user_id: str, prompt: str, priority: str) -> str:
    """
    Insert a new request row and move it from pending -> analyzing.
    Returns the request_id.
    """
    now = _utcnow_iso()
    response = with_retry(lambda:
        supabase.table("requests").insert({
            "user_id": user_id,
            "prompt": prompt,
            "priority": priority,
            "status": STATUS_PENDING,
            "created_at": now,
            "updated_at": now,
        }).execute()
    )
    request_id = response.data[0]["id"]

    with_retry(lambda:
        supabase.table("requests").update({
            "status": STATUS_ANALYZING,
            "updated_at": _utcnow_iso(),
        }).eq("id", request_id).execute()
    )

    log_event("request_created", request_id, {"priority": priority})
    return request_id

def set_request_status(supabase: Client, request_id: str, new_status: str) -> None:
    """
    Update status with a fresh updated_at.
    """
    with_retry(lambda:
        supabase.table("requests").update({
            "status": new_status,
            "updated_at": _utcnow_iso(),
        }).eq("id", request_id).execute()
    )

def set_scheduled_for(supabase: Client, request_id: str, scheduled_for_iso: str) -> None:
    """
    Persist a scheduled_for timestamp (ISO-8601, UTC recommended).
    """
    with_retry(lambda:
        supabase.table("requests").update({
            "scheduled_for": scheduled_for_iso,
            "updated_at": _utcnow_iso(),
        }).eq("id", request_id).execute()
    )

def get_user_email(supabase: Client, user_id: str) -> Optional[str]:
    res = with_retry(lambda:
        supabase.table("users")
        .select("email")
        .eq("id", user_id)
        .limit(1)
        .single()
        .execute()
    )
    row = res.data or {}
    email = (row or {}).get("email")
    return email if (isinstance(email, str) and "@" in email) else None

def set_notify_email(supabase: Client, request_id: str, email: Optional[str]) -> None:
    """
    Store a per-request notify email if requests.notify_email exists (TEXT, nullable).
    Falls back to request_note if the column doesn't exist.
    """
    if not email:
        return
    try:
        with_retry(lambda:
            supabase.table("requests").update({
                "notify_email": email,
                "updated_at": _utcnow_iso(),
            }).eq("id", request_id).execute()
        )
    except Exception:
        # Graceful fallback: append into request_note
        update_request_note(supabase, request_id, f"notify:{email}")

def update_after_analysis(
    supabase: Client,
    request_id: str,
    predictions: Dict,
    new_status: str,
    suggestions: Optional[List[str]] = None,
) -> None:
    """
    Persist predictions and status after analysis.
    NOTE: We do NOT set executed_at here. That's only set on finalize_execution.
    """
    update_raw: Dict[str, Any] = {
        "predicted_latency": int(predictions.get("latency_ms", 0)),
        "predicted_tokens": int(predictions.get("total_tokens", 0)),
        "predicted_complexity": float(predictions.get("complexity_score", 0.0)),
        # Optional: snapshot embedding if present
        "vector_embedding": predictions.get("vector_embedding"),
        "status": new_status,
        "updated_at": _utcnow_iso(),
    }

    # Write suggestions when explicitly provided (even if empty list)
    if suggestions is not None:
        update_raw["suggestions"] = [str(s) for s in suggestions]

    update = _omit_none(update_raw)

    with_retry(lambda:
        supabase.table("requests").update(update).eq("id", request_id).execute()
    )
    log_event("analysis_complete", request_id, {"status": new_status})

def update_request_note(
    supabase: Client,
    request_id: str,
    notes: Union[str, List[str]],
) -> None:
    """
    Append notes to request.request_note (newline-separated).
    Accepts a string or list of strings. Validates the request belongs to a verified user.
    """
    # normalize to list[str]
    notes_list = [notes] if isinstance(notes, str) else [n for n in notes if n]
    if not notes_list:
        return

    req_data = with_retry(lambda:
        supabase.table("requests")
        .select("user_id, request_note")
        .eq("id", request_id)
        .single()
        .execute()
    )
    row = req_data.data or {}
    if not row:
        raise HTTPException(status_code=404, detail="Request not found")
    if not row.get("user_id"):
        raise HTTPException(status_code=401, detail="Unauthorized: invalid or unverified user/API key.")

    # append rather than overwrite
    existing = row.get("request_note") or ""
    to_append = "\n".join(notes_list)
    new_note = existing + ("\n" if existing and to_append else "") + to_append

    with_retry(lambda:
        supabase.table("requests").update({
            "request_note": new_note,
            "updated_at": _utcnow_iso(),
        }).eq("id", request_id).execute()
    )

def finalize_execution(
    supabase: Client,
    request_id: str,
    execution_metrics: Dict,
    success: bool,
) -> None:
    """
    Write vector_index row, and mark the request as completed/failed.
    """
    # Prepare vector_index insert
    vector_insert: Dict[str, Union[str, int, float, List[float]]] = {
        "requests_id": request_id,
        "executed_end": execution_metrics.get("executed_end") or _utcnow_iso(),
        "actual_latency": int(execution_metrics.get("actual_latency", 0)),
        "actual_token_usage": int(execution_metrics.get("actual_token_usage", 0)),
        "answer": execution_metrics.get("answer"),
        "reasoning_summary": execution_metrics.get("reasoning_summary"),
    }

    # If you stored a snapshot embedding on the request, carry it into vector_index
    try:
        embedding_result = with_retry(lambda:
            supabase.table("requests")
            .select("vector_embedding")
            .eq("id", request_id)
            .single()
            .execute()
        )
        if embedding_result.data and embedding_result.data.get("vector_embedding") is not None:
            vector_insert["vector_embedding"] = embedding_result.data["vector_embedding"]
    except Exception:
        # Don't fail finalization just because of an embedding fetch error
        logger.exception("Failed to fetch vector_embedding for request_id=%s", request_id)

    # Insert vector record
    with_retry(lambda:
        supabase.table("vector_index").insert(vector_insert).execute()
    )

    # Flip request status and set executed_at now (only at completion)
    now = _utcnow_iso()
    with_retry(lambda:
        supabase.table("requests").update({
            "status": STATUS_COMPLETED if success else STATUS_FAILED,
            "executed_at": now,
            "updated_at": now,
        }).eq("id", request_id).execute()
    )

    log_event(
        "execution_finalized",
        request_id,
        {"status": STATUS_COMPLETED if success else STATUS_FAILED},
    )
