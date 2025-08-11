# api/workflow_requests.py

from datetime import datetime, timedelta
from typing import Optional, Dict

from fastapi import APIRouter, Depends, BackgroundTasks, Header, HTTPException
from supabase import Client

from auth import get_current_user, resolve_user_identity
from db.dependencies import get_supabase
from logic import predictor, suggester
from schemas import RequestCreate, RequestResponse, Suggestion
from services import request_handler, scheduler
from config import settings

router = APIRouter()

@router.post("/requests", response_model=RequestResponse)
async def create_request(
    request: RequestCreate,
    background_tasks: BackgroundTasks,
    current_user: Optional[Dict] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
    x_provided_user_id: Optional[str] = Header(None),
    x_force_db_timeout: Optional[str] = Header(None),       
    x_force_db_unavailable: Optional[str] = Header(None),   
):
    # --- prompt length guard ---
    if not request.prompt or len(request.prompt) < settings.prompt_min_chars:
        raise HTTPException(status_code=422, detail="Prompt is required")
    if len(request.prompt) > settings.prompt_max_chars:
        raise HTTPException(
            status_code=413,
            detail=f"Prompt too long (max {settings.prompt_max_chars} chars)"
        )
    # Debug-only: simulate DB timeout to validate 503/504 handling
    if settings.debug:
        if x_force_db_timeout == "1":
            # Simulate an upstream DB timeout -> 504
            raise HTTPException(status_code=504, detail="Upstream database timeout (simulated)")
        if x_force_db_unavailable == "1":
            # Simulate DB unreachable -> 503
            raise HTTPException(status_code=503, detail="Database temporarily unavailable (simulated)")
        
    """
    Resolve user -> create request -> predict -> pass/fail thresholds -> execute or suggest.
    User resolution precedence:
      1) provided_user_id (header > body metadata)  → upsert/reuse by external ID
      2) internal user_id (payload)                 → lookup by UUID (internal tools)
      3) API-key user                               → get_current_user()
      4) otherwise                                  → 401 Unauthorized (no anonymous fallback)
    """
    # ── 1) Resolve user identity ────────────────────────────────────────────────
    try:
        user_row, resolution_notes = resolve_user_identity(
            supabase, request, current_user, x_provided_user_id
        )
    except HTTPException as e:
        # Unverified user — return API error without storing in DB
        raise e

    user_id = user_row["id"]
    priority = request.priority or user_row.get("default_priority", "medium")

    # ── 2) Create request row (PENDING → ANALYZING) ─────────────────────────────
    request_id = request_handler.create_request(supabase, user_id, request.prompt, priority)

    # Store resolution notes only for verified users
    if resolution_notes:
        request_handler.update_request_note(supabase, request_id, resolution_notes)

    # ── 3) Synchronous prediction ───────────────────────────────────────────────
    predictions = predictor.analyze_request(request.prompt)

    # ── 4) Threshold evaluation ─────────────────────────────────────────────────
    result = predictor.check_thresholds(predictions, priority)
    now = datetime.utcnow()

    if result.passed:
        # Update request and queue async execution
        request_handler.update_after_analysis(supabase, request_id, predictions, "sent_to_execution")

        def dummy_llm_execution():
            import time, json
            time.sleep(1)  # Simulate delay
            print("✅ LLM execution starting...")
            with open("llm_fixed_answer.json") as f:
                metrics = json.load(f)
            metrics["executed_end"] = datetime.utcnow().isoformat()
            print("✅ Metrics loaded:", metrics)
            request_handler.finalize_execution(supabase, request_id, metrics, success=True)

        scheduler.enqueue_background_task(background_tasks, dummy_llm_execution)

        return RequestResponse(
            request_id=request_id,
            status="sent_to_execution",
            latency_estimate=predictions["latency_ms"],
            token_estimate=predictions["total_tokens"],
            complexity_score=predictions["complexity_score"],
            estimated_completion_time=now + timedelta(milliseconds=predictions["latency_ms"] + 300),
        )

    # Failed threshold → generate suggestions
    tips = suggester.generate_suggestions(request.prompt)
    request_handler.update_after_analysis(
        supabase, request_id, predictions,
        "below_threshold_suggestions_sent",
        suggestions=tips,
    )
    suggestion_objs = [Suggestion(title=tip, description=tip) for tip in tips]

    return RequestResponse(
        request_id=request_id,
        status="below_threshold_suggestions_sent",
        latency_estimate=predictions["latency_ms"],
        token_estimate=predictions["total_tokens"],
        complexity_score=predictions["complexity_score"],
        suggestions=suggestion_objs,
    )

@router.get("/requests/{request_id}")
async def get_request_status(
    request_id: str,
    supabase: Client = Depends(get_supabase),
):
    """
    Fetch request details suitable for clients (no embeddings).
    """
    res = (
        supabase.table("requests")
        .select(
            "id,user_id,prompt,"
            "predicted_latency,predicted_tokens,predicted_complexity,"
            "executed_at,suggestions,status,priority,request_note,"
            "updated_at,created_at"
        )
        .eq("id", request_id)
        .single()
        .execute()
    )

    if not res.data:
        raise HTTPException(status_code=404, detail="Request not found")

    return res.data

print("✅ workflow_requests router successfully loaded")
