# api/routes/workflow_requests.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, BackgroundTasks, Header, HTTPException, Query
from fastapi.responses import JSONResponse
from supabase import Client

from config import settings
from db.dependencies import get_supabase
from logic import predictor, suggester
from schemas import RequestCreate, RequestResponse, Suggestion
from services import request_handler, scheduler
from services.logger import log_event

# Auth: optional Supabase JWT + legacy precedence helpers
from auth import maybe_get_identity, get_current_user, resolve_user_identity
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
    ident=Depends(maybe_get_identity),                 # optional JWT identity
    current_user=Depends(get_current_user),            # optional API-key user
    x_provided_user_id: Optional[str] = Header(None),  # optional external id header
    x_force_db_timeout: Optional[str] = Header(None),  # debug only
    x_force_db_unavailable: Optional[str] = Header(None),  # debug only
):
    """
    Create a request -> analyze -> either (a) execute (immediate or scheduled)
    or (b) return suggestions when above thresholds.
    """

    # 0) Prompt guards
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

    # Debug-only fault injection
    if settings.debug:
        if x_force_db_timeout == "1":
            raise HTTPException(status_code=504, detail="Upstream database timeout (simulated)")
        if x_force_db_unavailable == "1":
            raise HTTPException(status_code=503, detail="Database temporarily unavailable (simulated)")

    # 1) Identity (AuthN + AuthZ)
    if ident and settings.debug is False:
        app_user = require_known_user_by_email(
            supabase,
            email=ident.email,
            provided_user_id=ident.user_id,  # optional first-time link
        )
    else:
        app_user, _notes = resolve_user_identity(
            supabase=supabase,
            request=request,                      # Pydantic model (has .metadata/.user_id)
            current_user=current_user,            # may be None
            x_provided_user_id=x_provided_user_id # header wins
        )

    user_id = app_user["id"]
    # ✅ define client_id **before** using it
    client_id = app_user.get("client_id")
    priority = request.priority or app_user.get("default_priority", "medium")

    # 2) Insert request row (pending → analyzing)
    request_id = request_handler.create_request(
        supabase=supabase,
        user_id=user_id,
        prompt=request.prompt,
        priority=priority,
        # client_name=app_user.get("client_name"),
    )

    # Pull client default optimize_for (if not provided)
    client_opt = None
    if client_id:
        cs = (
            supabase.table("client_settings")
            .select("optimize_for")
            .eq("client_id", client_id)
            .single()
            .execute()
            .data
        )
        client_opt = (cs or {}).get("optimize_for")

    # Final values to snapshot on the request
    model_name = getattr(request, "model_name", None)          # optional
    opt_for    = getattr(request, "optimize_for", None) or client_opt

    # Snapshot client + prefs on the request row
    supabase.table("requests").update({
        "client_id": client_id,
        "model_name": model_name,
        "optimize_for": opt_for,
    }).eq("id", request_id).execute()

    # Increment per-month usage counter for the client (simple, race-safe enough for now)
    if client_id:
        from datetime import date
        month = date.today().replace(day=1).isoformat()

        # Ensure row exists
        supabase.table("client_usage_counters").upsert(
            {"client_id": client_id, "month": month, "requests_count": 0},
            on_conflict="client_id,month"
        ).execute()

        # Fetch current count and bump
        cur = (
            supabase.table("client_usage_counters")
            .select("requests_count")
            .eq("client_id", client_id).eq("month", month)
            .single()
            .execute()
            .data
        ) or {"requests_count": 0}
        supabase.table("client_usage_counters").update(
            {"requests_count": int(cur.get("requests_count") or 0) + 1}
        ).eq("client_id", client_id).eq("month", month).execute()

    # Notify handling (verified email only)
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

    # 3) Predict metrics
    predictions = predictor.analyze_request(request.prompt)
    latency_ms = int(predictions.get("latency_ms", 0))
    token_estimate = int(predictions.get("total_tokens", 0))
    complexity = float(predictions.get("complexity_score", 0.0))

    # 4) Threshold evaluation
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

    # 5) Blocked → suggestions
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
    # 1) Base request row
    res = (
        supabase.table("requests")
        .select(
            "id,user_id,prompt,"
            "predicted_latency,predicted_tokens,predicted_complexity,"
            "executed_at,suggestions,status,priority,request_note,"
            "selected_child_request_id,"   # ✅ include this
            "updated_at,created_at"
        )
        .eq("id", request_id)
        .single()
        .execute()
    )

    if not res.data:
        raise HTTPException(status_code=404, detail="Request not found")

    row = res.data

    # 2) If it's a parent with a selected child, look up savings
    if row.get("selected_child_request_id"):
        sv = (
            supabase.table("request_estimate_savings")
            .select("parent_id, child_id, time_saved_ms, cost_saved_usd")
            .eq("parent_id", row["id"])
            .single()
            .execute()
            .data
        )
        if sv:
            # Attach to the response
            row["time_saved_ms"] = sv["time_saved_ms"]
            # Cast numeric → float if Supabase returns it as string
            row["cost_saved_usd"] = float(sv["cost_saved_usd"])
            row["selected_child_request_id"] = sv["child_id"]

    return row

@router.get("/requests", tags=["Requests"])
async def list_requests(
    supabase: Client = Depends(get_supabase),
    # filters
    user_id_like: Optional[str] = Query(None),
    q: Optional[str] = Query(None),  # search in prompt
    # sorting (fallback to created_at desc)
    sort_by: Optional[str] = Query("created_at"),
    sort_dir: Optional[str] = Query("desc"),  # 'asc'|'desc'
    # pagination
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
):
    sel = (
        supabase.table("requests")
        .select(
            "id,user_id,prompt,priority,status,"
            "predicted_latency,predicted_tokens,predicted_complexity,"
            "executed_at,suggestions,updated_at,created_at",
            count="exact"  # to get total rows
        )
    )

    if user_id_like:
        sel = sel.ilike("user_id", f"%{user_id_like}%")
    if q:
        sel = sel.ilike("prompt", f"%{q}%")

    # ordering
    sort_col = sort_by if sort_by in {
        "created_at","updated_at","predicted_latency","predicted_tokens","predicted_complexity","priority","status"
    } else "created_at"
    sel = sel.order(sort_col, desc=(sort_dir != "asc"))

    # pagination via range()
    start = (page - 1) * page_size
    end = start + page_size - 1
    res = sel.range(start, end).execute()
    items = res.data or []
    ids = [it["id"] for it in items]
    if ids:
        sv = (
            supabase.table("request_estimate_savings")
            .select("parent_id, child_id, time_saved_ms, cost_saved_usd")
            .in_("parent_id", ids)
            .execute()
            .data
        ) or []
        by_parent = {row["parent_id"]: row for row in sv}
        for it in items:
            s = by_parent.get(it["id"])
            if s:
                it["selected_child_request_id"] = s["child_id"]
                it["time_saved_ms"] = s["time_saved_ms"]
                it["cost_saved_usd"] = s["cost_saved_usd"]  # numeric may come back as string; ok

    return {
        "items": items,
        "total": res.count or 0,
        "page": page,
        "page_size": page_size,
        "sort_by": sort_col,
        "sort_dir": sort_dir,
    }

@router.get("/metrics", tags=["Requests"])
async def metrics(
    supabase: Client = Depends(get_supabase),
):
    def _range(days: int):
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()
        sel = supabase.table("requests").select(
            "predicted_latency,predicted_tokens,priority,status,executed_at"
        ).gte("created_at", since)
        return (sel.execute().data) or []

    def _calc(rows):
        # toy aggregation: total completed “time saved”/“cost saved” aren’t in schema,
        # so use simple proxies from predictions for now; you can refine later.
        total_latency_ms = sum(int(r.get("predicted_latency") or 0) for r in rows)
        total_tokens = sum(int(r.get("predicted_tokens") or 0) for r in rows)
        completed = sum(1 for r in rows if r.get("status") == "completed")
        return {
            "totalTimeSaved": max(0, total_latency_ms // 2),   # placeholder proxy
            "totalCostSaved": round(max(0, total_tokens * 0.000002), 2),  # proxy $
            "averageQualityLift": 0.0,       # no quality metric in schema yet
            "totalOptimizations": completed, # proxy count
        }

    m7  = _calc(_range(7))
    m30 = _calc(_range(30))
    # Year to date
    jan1 = datetime(datetime.utcnow().year, 1, 1).isoformat()
    rows_ytd = (supabase.table("requests").select(
        "predicted_latency,predicted_tokens,priority,status,executed_at"
    ).gte("created_at", jan1).execute().data) or []
    mytd = _calc(rows_ytd)

    return {"7d": m7, "30d": m30, "ytd": mytd}

@router.post("/requests/{parent_id}/select_child/{child_id}", tags=["Requests"])
async def select_child(
    parent_id: str,
    child_id: str,
    supabase: Client = Depends(get_supabase),
):
    # Verify the child belongs to the parent
    child = (
        supabase.table("requests")
        .select("id,parent_request_id")
        .eq("id", child_id)
        .single()
        .execute()
        .data
    ) or {}
    if child.get("parent_request_id") != parent_id:
        raise HTTPException(status_code=400, detail="Child does not belong to parent")

    # Mark the selection on the parent
    supabase.table("requests").update({
        "selected_child_request_id": child_id,
        "updated_at": datetime.utcnow().isoformat(),
    }).eq("id", parent_id).execute()

    return {"ok": True}

print("✅ workflow_requests router successfully loaded")
