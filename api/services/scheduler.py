# api/services/scheduler.py
from __future__ import annotations

"""
Durable job scheduler for TauLayer.

- Quick background tasks (FastAPI BackgroundTasks) for short, best-effort work
- Durable DB-backed queue (public.jobs) for ASAP or future-scheduled work
- Priority-aware leasing with SKIP LOCKED via RPC public.jobs_lease(...)
- Retries with exponential backoff, stale-lock release

Required DB objects:
  - table public.jobs (id, request_id, status, priority, run_at, attempts, last_error, locked_by, locked_at, created_at, updated_at)
  - function public.jobs_lease(p_worker_id text, p_limit int, p_lock_expired_before timestamptz) RETURNS SETOF public.jobs
    (see SQL we shared earlier)

Environment-driven knobs are read from config.settings (with safe defaults).
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Union

# -------- Logging -------------------------------------------------------------

logger = logging.getLogger(__name__)
try:
    # Optional: if you have a structured logger helper
    from services.logger import log as _structured_log
except Exception:
    _structured_log = None

def _log(level: str, msg: str, **extra):
    if _structured_log:
        getattr(_structured_log, level, _structured_log.info)(msg, extra=extra or None)
    else:
        getattr(logger, level if hasattr(logger, level) else "info")(f"{msg} | {extra}")

# -------- FastAPI helper: short background tasks ------------------------------

try:
    from fastapi import BackgroundTasks
except Exception:
    BackgroundTasks = None  # type: ignore


def enqueue_background_task(background_tasks: "BackgroundTasks", task_fn, *args, **kwargs) -> None:
    """
    Fire-and-forget in-process work for SHORT tasks only.
    Use the durable queue for heavy/long/scheduled jobs.
    """
    if BackgroundTasks is None:
        raise RuntimeError("FastAPI not available: BackgroundTasks cannot be used here.")
    _log("info", "enqueue_background_task", task=task_fn.__name__)
    background_tasks.add_task(task_fn, *args, **kwargs)

# -------- Durable queue: Supabase client & settings ---------------------------

from db.dependencies import get_supabase
from config import settings

# Knobs (with safe defaults if missing in env)
MAX_ATTEMPTS: int      = getattr(settings, "queue_max_attempts", 5)
BATCH_SIZE: int        = getattr(settings, "queue_batch_size", 10)
LOCK_TTL_SEC: int      = getattr(settings, "queue_lock_ttl_sec", 120)
BACKOFF_BASE_SEC: int  = getattr(settings, "queue_backoff_base_sec", 15)
BACKOFF_CAP_SEC: int   = getattr(settings, "queue_backoff_cap_sec", 600)

# Name of the Postgres RPC that leases jobs using FOR UPDATE SKIP LOCKED
JOBS_LEASE_RPC_NAME = "jobs_lease"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _coerce_uuid_str(val: Union[str, uuid.UUID]) -> str:
    return str(val) if isinstance(val, uuid.UUID) else (val or "")


def _next_run_at(attempts: int) -> datetime:
    """Exponential backoff with cap."""
    delay = min(BACKOFF_BASE_SEC * (2 ** max(0, attempts - 1)), BACKOFF_CAP_SEC)
    return _utcnow() + timedelta(seconds=delay)

# -------- Public API: enqueue, schedule, lease, complete, fail, release -------

async def enqueue_job(
    request_id: Union[str, uuid.UUID],
    priority: str = "medium",
    run_at: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Create/Upsert a durable job row for the given request_id.
    - If run_at is None -> run ASAP
    - If run_at is in the future -> schedule for later
    One job per request_id (unique).
    """
    sb = get_supabase()
    rid = _coerce_uuid_str(request_id)
    run_at = run_at or _utcnow()
    data = {
        "request_id": rid,
        "status": "queued",
        "priority": priority,
        "run_at": run_at.isoformat(),
        "attempts": 0,
        "last_error": None,
        "locked_by": None,
        "locked_at": None,
    }
    _log("info", "enqueue_job", request_id=rid, priority=priority, run_at=str(run_at))
    res = sb.table("jobs").upsert(data, on_conflict="request_id").execute()
    return (res.data or [{}])[0]


async def schedule_for_later(
    request_id: Union[str, uuid.UUID],
    priority: str,
    run_at: datetime,
) -> Dict[str, Any]:
    """
    Convenience wrapper for enqueueing a job with a future run time.
    """
    if run_at.tzinfo is None:
        # Treat naive as UTC to avoid timezone ambiguity
        run_at = run_at.replace(tzinfo=timezone.utc)
    return await enqueue_job(request_id=request_id, priority=priority, run_at=run_at)


async def lease_jobs(worker_id: str, limit: int = BATCH_SIZE) -> List[Dict[str, Any]]:
    """
    Atomically lease ready jobs using SKIP LOCKED via RPC public.jobs_lease(...).
    Only jobs with status='queued' AND run_at <= now() are leased.
    Returns the leased job rows with status flipped to 'running' and lock set.
    """
    sb = get_supabase()
    limit = max(1, min(int(limit), 100))
    lock_expiry = (_utcnow() - timedelta(seconds=LOCK_TTL_SEC)).isoformat()

    _log("info", "lease_jobs.call", worker_id=worker_id, limit=limit, lock_exp_before=lock_expiry)
    res = sb.rpc(
        JOBS_LEASE_RPC_NAME,
        {
            "p_worker_id": worker_id,
            "p_limit": limit,
            "p_lock_expired_before": lock_expiry,
        },
    ).execute()

    jobs = res.data or []
    _log("info", "lease_jobs.result", leased=len(jobs))
    return jobs


async def complete_job(job_id: Union[str, uuid.UUID]) -> Dict[str, Any]:
    """
    Mark a job as completed and release its lock.
    """
    sb = get_supabase()
    jid = _coerce_uuid_str(job_id)
    _log("info", "complete_job", job_id=jid)
    res = sb.table("jobs").update({
        "status": "completed",
        "locked_by": None,
        "locked_at": None,
        "updated_at": _utcnow().isoformat(),
    }).eq("id", jid).execute()
    return (res.data or [{}])[0]


async def fail_and_reschedule(job_id: Union[str, uuid.UUID], error_message: str) -> Dict[str, Any]:
    """
    Increment attempt count and either:
      - reschedule with backoff (status -> 'queued'), or
      - mark as 'failed' if attempts exceed MAX_ATTEMPTS.
    """
    sb = get_supabase()
    jid = _coerce_uuid_str(job_id)

    # Read current attempts
    cur = sb.table("jobs").select("attempts").eq("id", jid).single().execute().data or {}
    attempts = int(cur.get("attempts", 0)) + 1

    if attempts >= MAX_ATTEMPTS:
        _log("warning", "job_failed_permanent", job_id=jid, attempts=attempts, error=error_message)
        res = sb.table("jobs").update({
            "status": "failed",
            "attempts": attempts,
            "last_error": error_message,
            "locked_by": None,
            "locked_at": None,
            "updated_at": _utcnow().isoformat(),
        }).eq("id", jid).execute()
        return (res.data or [{}])[0]

    next_time = _next_run_at(attempts)
    _log("warning", "job_rescheduled", job_id=jid, attempts=attempts, next_run_at=str(next_time), error=error_message)
    res = sb.table("jobs").update({
        "status": "queued",
        "attempts": attempts,
        "last_error": error_message,
        "locked_by": None,
        "locked_at": None,
        "run_at": next_time.isoformat(),
        "updated_at": _utcnow().isoformat(),
    }).eq("id", jid).execute()
    return (res.data or [{}])[0]


async def release_stale_locks() -> int:
    """
    Safety valve: Any job stuck 'running' longer than LOCK_TTL_SEC
    is returned to the queue as 'queued' with run_at=now().
    Returns count of rows updated (best-effort).
    """
    sb = get_supabase()
    cutoff = (_utcnow() - timedelta(seconds=LOCK_TTL_SEC)).isoformat()
    _log("info", "release_stale_locks.call", cutoff=cutoff)
    res = sb.table("jobs").update({
        "status": "queued",
        "locked_by": None,
        "locked_at": None,
        "run_at": _utcnow().isoformat(),
    }).lte("locked_at", cutoff).eq("status", "processing").execute()
    updated = len(res.data or [])
    _log("info", "release_stale_locks.result", updated=updated)
    return updated
