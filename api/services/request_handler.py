# api/services/request_handler.py

from supabase import Client
from datetime import datetime
from typing import Optional, Dict
from uuid import UUID
from fastapi import HTTPException
from services.logger import log_event
import logging
logger = logging.getLogger(__name__)

STATUS_PENDING = "pending"
STATUS_ANALYZING = "analyzing"
STATUS_EXECUTION = "sent_to_execution"
STATUS_PROCESSING = "processing"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
STATUS_BELOW_THRESHOLD = "below_threshold_suggestions_sent"


def get_user_by_id(supabase: Client, user_id: UUID):
    try:
        res = (
            supabase.table("users")
            .select("id, default_priority")
            .eq("id", str(user_id))
            .limit(1)
            .execute()
        )
        # [] => not found (let caller raise 404); [row] => return row dict
        return res.data[0] if res.data else None
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Supabase error in get_user_by_id({user_id}): {e}")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable: user lookup failed.")


def get_user_by_external_id(supabase: Client, ext_id: str):
    try:
        res = (
            supabase.table("users")
            .select("id, default_priority")
            .eq("provided_user_id", ext_id)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Supabase error in get_user_by_external_id({ext_id}): {e}")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable: user lookup failed.")


def update_request_note(supabase: Client, request_id: str, notes: list[str]):
    """
    Update request_note in requests — only if the request belongs to a verified user.
    For unauthenticated calls, return an API error but do not persist in DB.
    """
    if not notes:
        return

    # Check if request has a valid user_id
    req_data = (
        supabase.table("requests")
        .select("user_id")
        .eq("id", request_id)
        .single()
        .execute()
    )

    if not req_data.data:
        raise HTTPException(status_code=404, detail="Request not found")
    if not req_data.data.get("user_id"):
        raise HTTPException(status_code=401, detail="Unauthorized: invalid or unverified user/API key.")

    # Verified user → store actual error notes in DB
    supabase.table("requests").update({
        "request_note": "\n".join(notes)
    }).eq("id", request_id).execute()


def upsert_user_by_external_id(
    supabase: Client,
    ext_id: str,
    default_priority: str = "medium",
    user_type: str = "other",
):
    """
    Ensure a user exists for provided_user_id. Create if missing, return {id, default_priority}.
    """
    supabase.table("users").upsert(
        {
            "provided_user_id": ext_id,
            "type": user_type,
            "default_priority": default_priority,
        },
        on_conflict="provided_user_id",
    ).execute()

    res = supabase.table("users")\
        .select("id, default_priority")\
        .eq("provided_user_id", ext_id)\
        .single()\
        .execute()
    return res.data if res.data else None


def create_request(supabase: Client, user_id: str, prompt: str, priority: str) -> str:
    """
    Insert a new request row with PENDING status, then update to ANALYZING.
    Returns the new request ID.
    """
    now = datetime.utcnow().isoformat()

    response = supabase.table("requests").insert({
        "user_id": user_id,
        "prompt": prompt,
        "priority": priority,
        "status": STATUS_PENDING,
        "created_at": now,
        "updated_at": now,
    }).execute()

    request_id = response.data[0]["id"]

    supabase.table("requests").update({
        "status": STATUS_ANALYZING,
        "updated_at": now,
    }).eq("id", request_id).execute()

    log_event("request_created", request_id, {"priority": priority})
    return request_id


def update_after_analysis(
    supabase: Client,
    request_id: str,
    predictions: Dict,
    new_status: str,
    suggestions: Optional[list] = None
):
    """
    Record predictions and status after analysis phase.
    Optionally record suggestions if provided (for failed threshold).
    """
    update = {
        "predicted_latency": predictions["latency_ms"],
        "predicted_tokens": predictions["total_tokens"],
        "predicted_complexity": predictions["complexity_score"],
        "vector_embedding": predictions["vector_embedding"],
        "status": new_status,
    }

    if new_status == STATUS_EXECUTION:
        update["executed_at"] = datetime.utcnow().isoformat()

    if suggestions:
        update["suggestions"] = suggestions

    supabase.table("requests").update(update).eq("id", request_id).execute()
    log_event("analysis_complete", request_id, {"status": new_status})


def finalize_execution(
    supabase: Client,
    request_id: str,
    execution_metrics: Dict,
    success: bool
):
    """
    Store execution results and update final status.
    """
    vector_insert = {
        "requests_id": request_id,
        "executed_end": execution_metrics["executed_end"],
        "actual_latency": execution_metrics["actual_latency"],
        "actual_token_usage": execution_metrics["actual_token_usage"],
        "answer": execution_metrics.get("answer", None),
        "reasoning_summary": execution_metrics.get("reasoning_summary", None),
        "recommendations_for_improvement": execution_metrics.get("recommendations_for_improvement", []),
    }

    # Copy the embedding from requests if present
    embedding_result = supabase.table("requests").select("vector_embedding")\
        .eq("id", request_id).execute()
    if embedding_result.data:
        vector_insert["vector_embedding"] = embedding_result.data[0]["vector_embedding"]

    supabase.table("vector_index").insert(vector_insert).execute()

    supabase.table("requests").update({
        "status": STATUS_COMPLETED if success else STATUS_FAILED,
        "updated_at": datetime.utcnow().isoformat(),
    }).eq("id", request_id).execute()

    log_event("execution_finalized", request_id, {
        "status": STATUS_COMPLETED if success else STATUS_FAILED
    })
