# api/routes/client.py
from __future__ import annotations

from datetime import date
from typing import Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from db.dependencies import get_supabase
from auth import get_current_user, maybe_get_identity  # <- include maybe_get_identity

router = APIRouter()

# ---------- small helpers ----------

def _first_or_none(q):
    """
    Execute a PostgREST select builder with limit(1) and return the first row or None.
    Usage: _first_or_none(supabase.table("t").select("*").eq("col", v))
    """
    res = q.limit(1).execute()
    rows = res.data or []
    return rows[0] if isinstance(rows, list) and rows else None

def _resolve_client_id(
    supabase: Client,
    ident: Optional[dict],
    current_user: Optional[dict],
) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Resolve (client_id, client_name, user_email) from either:
      1) API key user (current_user) with client_id, or
      2) Supabase JWT identity (ident) via email lookup in public.users.
    """
    # 1) API-key user takes precedence if it has a client_id
    if current_user and current_user.get("client_id"):
        cid = current_user["client_id"]
        c = _first_or_none(
            supabase.table("clients").select("id,name").eq("id", cid)
        )
        return cid, (c or {}).get("name"), None

    # 2) Supabase JWT email
    if ident and ident.get("email"):
        email = ident["email"]
        u = _first_or_none(
            supabase.table("users")
            .select("client_id, client_name, email")
            .ilike("email", email)  # exact match is fine; ilike supports it
        )
        if not u or not u.get("client_id"):
            raise HTTPException(status_code=404, detail="User has no client")

        cid = u["client_id"]
        cname = u.get("client_name")
        if not cname:
            c = _first_or_none(
                supabase.table("clients").select("id,name").eq("id", cid)
            )
            cname = (c or {}).get("name")
        return cid, cname, email

    # 3) No identity
    raise HTTPException(status_code=401, detail="Missing identity")

# ---------- routes ----------

@router.get("/client/me")
async def get_client_profile(
    supabase: Client = Depends(get_supabase),
    current_user=Depends(get_current_user),
    ident=Depends(maybe_get_identity),
):
    client_id, client_name, user_email = _resolve_client_id(supabase, ident, current_user)

    # Billing/settings/usage are optional — return {} / 0 when missing.
    billing = _first_or_none(
        supabase.table("client_billing").select("*").eq("client_id", client_id)
    ) or {}

    settings = _first_or_none(
        supabase.table("client_settings").select("*").eq("client_id", client_id)
    ) or {}

    month = date.today().replace(day=1).isoformat()
    usage_row = _first_or_none(
        supabase.table("client_usage_counters")
        .select("requests_count")
        .eq("client_id", client_id)
        .eq("month", month)
    ) or {"requests_count": 0}

    models = (
        supabase.table("client_models")
        .select("model_key,display_name,is_active")
        .eq("client_id", client_id)
        .eq("is_active", True)
        .execute()
        .data
        or []
    )

    return {
        "client_id": client_id,
        "client": {"id": client_id, "name": client_name},
        "user": {"email": user_email},
        "billing": billing,
        "settings": settings,
        "usage": {"month": month, "requests_this_month": int(usage_row.get("requests_count") or 0)},
        "models": models,
    }

@router.put("/client/settings")
async def update_client_settings(
    payload: dict,
    supabase: Client = Depends(get_supabase),
    current_user=Depends(get_current_user),
    ident=Depends(maybe_get_identity),
):
    client_id, _, _ = _resolve_client_id(supabase, ident, current_user)

    update = {}
    if "config_yaml" in payload:   update["config_yaml"] = payload["config_yaml"]
    if "optimize_for" in payload:  update["optimize_for"] = payload["optimize_for"]
    if not update: return {"ok": True}

    update["updated_at"] = "now()"  # will be stringified; ok for PostgREST if you prefer real timestamp use server default
    supabase.table("client_settings").upsert(
        {"client_id": client_id, **update}, on_conflict="client_id"
    ).execute()
    return {"ok": True}

@router.put("/client/billing")
async def update_client_billing(
    payload: dict,
    supabase: Client = Depends(get_supabase),
    current_user=Depends(get_current_user),
    ident=Depends(maybe_get_identity),
):
    client_id, _, _ = _resolve_client_id(supabase, ident, current_user)

    update = {}
    for k in ("billing_email","plan","monthly_quota","next_billing_date"):
        if k in payload: update[k] = payload[k]
    if not update: return {"ok": True}

    update["updated_at"] = "now()"
    supabase.table("client_billing").upsert(
        {"client_id": client_id, **update}, on_conflict="client_id"
    ).execute()
    return {"ok": True}

@router.get("/client/models")
async def list_client_models(
    supabase: Client = Depends(get_supabase),
    current_user=Depends(get_current_user),
    ident=Depends(maybe_get_identity),
):
    client_id, _, _ = _resolve_client_id(supabase, ident, current_user)
    rows = (
        supabase.table("client_models")
        .select("model_key,display_name,is_active")
        .eq("client_id", client_id)
        .execute()
        .data
        or []
    )
    return rows
