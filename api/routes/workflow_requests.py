# api/routes/workflow_requests.py
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, BackgroundTasks, Header, HTTPException
from fastapi.responses import JSONResponse
from supabase import Client

from db.dependencies import get_supabase
from logic import predictor, suggester
from schemas import RequestCreate, RequestResponse, Suggestion
from services import request_handler, scheduler
from config import settings
from services.logger import log_event

# NEW: Supabase JWT identity + email-allowlist guard
from auth import get_identity
from services.request_handler import require_known_user_by_email

router = APIRouter()

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

def _to_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

@router.post("/requests", response_model=RequestResponse)
async def create_request(
    request: RequestCreate,
    background_tasks: BackgroundTasks,
    supabase: Client = Depends(get_supabase),
    ident = Depends(get_identity),                      # ← validated {user_id,email}
    x_force_db_timeout: Optional[str] = Header(None),   # debug only
    x_force_db_unavailable: Optional[str] = Header(None),  # debug only
):
    """
    Create a request -> analyze -> either (a) execute (immediate or scheduled)
    or (b) return suggestions when above thresholds.
    """

    # ── 0) Prompt guards ───────────────────────────────────────────────────────
    if not request.prompt or len(request.prompt) < settings.prompt_min_chars:
        return JSONResponse(
            status_code=422,
            content={
                "status": "error",
                "error": "Prompt is required",
                "hint": f"Add at least {settings.prompt_min_chars} characters of detail.",
            },
        )
    if len(request.prompt) > settings.prompt_max_chars:
        return JSONResponse(
            status_code=413,
            content={
                "status": "error",
                "error": f"Prompt too long (max {settings.prompt_max_chars} chars).",
                "your_length": len(request.prompt),
                "max_chars": settings.prompt_max_chars,
                "how_to_fix": [
                    "Shorten your request (remove boilerplate or unrelated context).",
                    "Split into multiple smaller requests.",
                    "If this is heavy work, resubmit with a shorter prompt and set a future 'scheduled_for' time.",
                ],
            },
        )

    # ── Debug-only fault injection ─────────────────────────────────────────────
    if settings.debug:
        if x_force_db_timeout == "1":
            raise HTTPException(status_code=504, detail="Upstream database timeout (simulated)")
        if x_force_db_unavailable == "1":
            raise HTTPException(status_code=503, detail="Database temporarily unavailable (simulated)")

    # ── 1) Identity: invite-only by email in public.users ─────────────────────
    app_user = require_known_user_by_email(
        supabase,
        email=ident.email,
        provided_user_id=ident.user_id,      # optional first-time link
    )
    user_id = app_user["id"]
    priority = request.priority or app_user.get("default_priority", "medium")

    # ── 2) Insert request row (pending → analyzing) ────────────────────────────
    request_id = request_handler.create_request(
        supabase=supabase,
        user_id=user_id,
        prompt=request.prompt,
        priority=priority,
        # client_name=app_user.get("client_name"),  # uncomment when column exists on requests
    )

    # ── Notify handling (verified email only) ─────────────────────────────────
    wants_notify = False
    if request.metadata and isinstance(request.metadata, dict):
        wants_notify = bool(request.metadata.get("notify")) or bool(request.metadata.get("notify_me"))

    if wants_notify:
        verified_email = request_handler.get_user_email(supabase, user_id)
        if verified_email:
            request_handler.set_notify_email(supabase, request_id, verified_email)
            request_handler.update_request_note(supabase, request_id, f"notify:{verified_email}")
        else:
            request_handler.update_request_note(supabase, request_id, "notify_requested_but_no_verified_email")

    # ── 3) Predict metrics ─────────────────────────────────────────────────────
    predictions = predictor.analyze_request(request.prompt)
    latency_ms = int(predictions.get("latency_ms", 0))
    token_estimate = int(predictions.get("total_tokens", 0))
    complexity = float(predictions.get("complexity_score", 0.0))

    # ── 4) Threshold evaluation ────────────────────────────────────────────────
    decision = predictor.check_thresholds(predictions, priority)

    exceeded = getattr(decision, "exceeded_dimensions", []) or []
    log_event(
        "threshold_decision",
        request_id,
        {
            "priority": priority,
            "predicted_tokens": token_estimate,
            "predicted_latency_ms": latency_ms,
            "predicted_complexity": complexity,
            "exceeded_dimensions": exceeded,
            "decision": "approve" if decision.passed else "block",
        },
    )

    if decision.passed:
        request_handler.update_after_analysis(
            supabase,
            request_id=request_id,
            predictions=predictions,
            new_status="sent_to_execution",
        )

        scheduled_for = _to_utc(request.scheduled_for)
        if scheduled_for and scheduled_for > _utcnow():
            await scheduler.schedule_for_later(
                request_id=request_id,
                priority=priority,
                run_at=scheduled_for,
            )
            request_handler.set_scheduled_for(supabase, request_id, scheduled_for.isoformat())
            return RequestResponse(
                request_id=request_id,
                status="sent_to_execution",
                latency_estimate=latency_ms,
                token_estimate=token_estimate,
                complexity_score=complexity,
                estimated_completion_time=scheduled_for,
                suggestions=None,
            )

        heavy_cutoff_ms = getattr(settings, "background_max_latency_ms", 2000)
        if latency_ms <= heavy_cutoff_ms:
            def _dummy_llm_execution():
                import time, json
                time.sleep(1)
                with open("llm_fixed_answer.json") as f:
                    metrics = json.load(f)
                metrics["executed_end"] = _utcnow().isoformat()
                request_handler.finalize_execution(
                    supabase=supabase,
                    request_id=request_id,
                    execution_metrics=metrics,
                    success=True,
                )

            scheduler.enqueue_background_task(background_tasks, _dummy_llm_execution)
            eta = _utcnow() + timedelta(milliseconds=latency_ms + 300)
        else:
            await scheduler.enqueue_job(
                request_id=request_id,
                priority=priority,
                run_at=None,
            )
            eta = _utcnow() + timedelta(milliseconds=latency_ms)

        return RequestResponse(
            request_id=request_id,
            status="sent_to_execution",
            latency_estimate=latency_ms,
            token_estimate=token_estimate,
            complexity_score=complexity,
            estimated_completion_time=eta,
            suggestions=None,
        )

    # ── 5) Blocked → generate actionable suggestions ───────────────────────────
    tips = suggester.generate_suggestions(request.prompt)
    request_handler.update_after_analysis(
        supabase,
        request_id=request_id,
        predictions=predictions,
        new_status="below_threshold_suggestions_sent",
        suggestions=tips,
    )
    suggestion_objs = [Suggestion(title=tip, description=tip) for tip in tips]

    return RequestResponse(
        request_id=request_id,
        status="below_threshold_suggestions_sent",
        latency_estimate=latency_ms,
        token_estimate=token_estimate,
        complexity_score=complexity,
        suggestions=suggestion_objs,
    )

@router.get("/requests/{request_id}")
async def get_request_status(
    request_id: str,
    supabase: Client = Depends(get_supabase),
):
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
