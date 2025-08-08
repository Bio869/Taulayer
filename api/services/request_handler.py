# api/services/request_handler.py

from supabase import Client
from datetime import datetime
from typing import Optional, Dict

from services.logger import log_event

STATUS_PENDING = "pending"
STATUS_ANALYZING = "analyzing"
STATUS_EXECUTION = "sent_to_execution"
STATUS_PROCESSING = "processing"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
STATUS_BELOW_THRESHOLD = "below_threshold_suggestions_sent"


def create_request(supabase: Client, user_id: str, prompt: str, priority: str) -> str:
    """
    Insert a new request row with PENDING status, then update to ANALYZING.
    """
    now = datetime.utcnow().isoformat()
    response = supabase.table("requests").insert({
        "user_id": user_id,
        "prompt": prompt,
        "priority": priority,
        "status": STATUS_PENDING,
        "created_at": now,
        "updated_at": now
    }).execute()

    request_id = response.data[0]["id"]

    supabase.table("requests").update({
        "status": STATUS_ANALYZING,
        "updated_at": now
    }).eq("id", request_id).execute()

    log_event("request_created", request_id, {"priority": priority})
    return request_id


def update_after_analysis(supabase: Client, request_id: str, predictions: Dict, new_status: str, suggestions: Optional[list] = None):
    """
    Record predictions and status after analysis phase.
    Optionally record suggestions if provided (for failed threshold).
    """
    update = {
        "predicted_latency": predictions["latency_ms"],
        "predicted_tokens": predictions["total_tokens"],
        "predicted_complexity": predictions["complexity_score"],
        "vector_embedded": predictions["vector_embedded"],
        "status": new_status,
        "updated_at": datetime.utcnow().isoformat()
    }

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
        "reasoning_summary": execution_metrics.get("reasoning_summary", None),
        "recommendations_for_improvement": execution_metrics.get("recommendations_for_improvement", [])
    }
    supabase.table("vector_index").insert(vector_insert).execute()

    supabase.table("requests").update({
        "status": STATUS_COMPLETED if success else STATUS_FAILED,
        "updated_at": datetime.utcnow().isoformat()
    }).eq("id", request_id).execute()

    log_event("execution_finalized", request_id, {"status": "completed" if success else "failed"})
