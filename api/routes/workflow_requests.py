# api/workflow_requests.py

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, BackgroundTasks, Header, HTTPException
from supabase import Client

from auth import get_current_user, resolve_user_identity
from db.dependencies import get_supabase
from logic import predictor, suggester
from schemas import RequestCreate, RequestResponse, Suggestion
from services import request_handler, scheduler
from config import settings

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
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
    x_provided_user_id: Optional[str] = Header(None),
    x_force_db_timeout: Optional[str] = Header(None),       # debug only
    x_force_db_unavailable: Optional[str] = Header(None),   # debug only
):
    """
    Create a request -> analyze -> either (a) execute (immediate or scheduled)
    or (b) return suggestions when above thresholds.
    """

    # ── 0) Prompt guards ───────────────────────────────────────────────────────
    if not request.prompt or len(request.prompt) < settings.prompt_min_chars:
        raise HTTPException(status_code=422, detail="Prompt is required")
    if len(request.prompt) > settings.prompt_max_chars:
        raise HTTPException(status_code=413, detail=f"Prompt too long (max {settings.prompt_max_chars} chars)")

    # Debug-only fault injection
    if settings.debug:
        if x_force_db_timeout == "1":
            raise HTTPException(status_code=504, detail="Upstream database timeout (simulated)")
        if x_force_db_unavailable == "1":
            raise HTTPException(status_code=503, detail="Database temporarily unavailable (simulated)")

    # ── 1) Resolve identity (header > payload user_id > API key) ──────────────
    try:
        user_row, resolution_notes = resolve_user_identity(
            supabase, request, current_user, x_provided_user_id
        )
    except HTTPException as e:
        # Identity failure → do not persist anything
        raise e

    user_id = user_row["id"]
    priority = request.priority or user_row.get("default_priority", "medium")

    # ── 2) Insert request row (pending → analyzing) ────────────────────────────
    request_id = request_handler.create_request(
        supabase=supabase,
        user_id=user_id,
        prompt=request.prompt,
        priority=priority,
    )

    # Optional: store notify email hint if provided in metadata
    notify_email = None
    if request.metadata and isinstance(request.metadata, dict):
        notify_email = request.metadata.get("notify_email")
        if notify_email:
            request_handler.update_request_note(
                supabase, request_id, f"notify:{notify_email}"
            )

    if resolution_notes:
        # append (don’t overwrite) resolution notes
        request_handler.update_request_note(
            supabase,
            request_id,
            (resolution_notes if not notify_email else f"{resolution_notes}; notify:{notify_email}")
        )

    # ── 3) Predict metrics ─────────────────────────────────────────────────────
    predictions = predictor.analyze_request(request.prompt)
    # Normalized numbers we’ll reuse
    latency_ms = int(predictions.get("latency_ms", 0))
    token_estimate = int(predictions.get("total_tokens", 0))
    complexity = float(predictions.get("complexity_score", 0.0))

    # ── 4) Threshold evaluation ────────────────────────────────────────────────
    decision = predictor.check_thresholds(predictions, priority)
    now = _utcnow()

    if decision.passed:
        # Persist predictions + mark as moving to execution path
        request_handler.update_after_analysis(
            supabase,
            request_id=request_id,
            predictions=predictions,
            new_status="sent_to_execution",   # external contract remains
        )

        # If caller requested a future time, schedule durably
        scheduled_for = _to_utc(request.scheduled_for)

        if scheduled_for and scheduled_for > now:
            # Durable schedule for later using the jobs queue
            await scheduler.schedule_for_later(
                request_id=request_id,
                priority=priority,
                run_at=scheduled_for,
            )
            # Return response indicating it’s going to execute (at/after scheduled time)
            return RequestResponse(
                request_id=request_id,
                status="sent_to_execution",
                latency_estimate=latency_ms,
                token_estimate=token_estimate,
                complexity_score=complexity,
                estimated_completion_time=scheduled_for,
                suggestions=None,
            )

        # Otherwise decide immediate path: short = BackgroundTasks; heavy = durable queue
        # Heuristic: anything over ~2s should be durable to avoid tying it to the HTTP worker
        heavy_cutoff_ms = getattr(settings, "background_max_latency_ms", 2000)

        if latency_ms <= heavy_cutoff_ms:
            # Fire-and-forget short task (best-effort)
            def _dummy_llm_execution():
                import time, json
                time.sleep(1)  # simulate a quick run
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
            eta = now + timedelta(milliseconds=latency_ms + 300)
        else:
            # Durable ASAP via jobs queue
            await scheduler.enqueue_job(
                request_id=request_id,
                priority=priority,
                run_at=None,  # ASAP
            )
            eta = now + timedelta(milliseconds=latency_ms)

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
        new_status="sent_to_execution",   # external contract remains
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


# Helpful log so you know the router loaded in dev
print("✅ workflow_requests router successfully loaded")
