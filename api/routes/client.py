# api/routes/client.py
from fastapi import APIRouter, Depends, HTTPException
from db.dependencies import get_supabase
from auth import get_current_user, maybe_get_identity
from supabase import Client
from datetime import date

router = APIRouter()

def _resolve_client_ctx(supabase: Client, ident: dict | None, current_user: dict | None) -> dict:
    """
    Return {'client_id','client_name','user_email'} for either:
      - Supabase JWT user (email) or
      - API-key user (client_id on the row)
    """
    # 1) Supabase-auth user (email from JWT)
    if ident and isinstance(ident, dict) and ident.get("email"):
        u = (
            supabase.table("users")
            .select("client_id, client_name, email")
            .ilike("email", ident["email"])
            .single()
            .execute()
            .data
        ) or {}
        if u.get("client_id"):
            return {
                "client_id": u["client_id"],
                "client_name": u.get("client_name"),
                "user_email": ident["email"],
            }

    # 2) API-key user
    if current_user and current_user.get("client_id"):
        c = (
            supabase.table("clients")
            .select("name")
            .eq("id", current_user["client_id"])
            .single()
            .execute()
            .data
        ) or {}
        return {
            "client_id": current_user["client_id"],
            "client_name": c.get("name"),
            "user_email": None,
        }

    raise HTTPException(status_code=404, detail="User has no client")

@router.get("/client/me")
async def get_client_profile(
    supabase: Client = Depends(get_supabase),
    ident=Depends(maybe_get_identity),            # ✅ allow Supabase JWT users
    current_user=Depends(get_current_user),       # ✅ or API-key users
):
    ctx = _resolve_client_ctx(supabase, ident, current_user)
    client_id = ctx["client_id"]

    billing = (supabase.table("client_billing")
               .select("*").eq("client_id", client_id).single().execute().data) or {}
    settings = (supabase.table("client_settings")
                .select("*").eq("client_id", client_id).single().execute().data) or {}

    month = date.today().replace(day=1).isoformat()
    usage = (supabase.table("client_usage_counters")
             .select("requests_count")
             .eq("client_id", client_id).eq("month", month)
             .single().execute().data) or {"requests_count": 0}

    models = (supabase.table("client_models")
              .select("model_key,display_name,is_active")
              .eq("client_id", client_id).eq("is_active", True)
              .execute().data) or []

    return {
        "client": {"id": client_id, "name": ctx.get("client_name")},
        "user":   {"email": ctx.get("user_email")},
        "billing": billing,
        "settings": settings,
        "usage": {"month": month, "requests_this_month": usage.get("requests_count", 0)},
        "models": models,
    }

@router.put("/client/settings")
async def update_client_settings(
    payload: dict,
    supabase: Client = Depends(get_supabase),
    ident=Depends(maybe_get_identity),
    current_user=Depends(get_current_user),
):
    ctx = _resolve_client_ctx(supabase, ident, current_user)
    update = {}
    if "config_yaml" in payload:  update["config_yaml"] = payload["config_yaml"]
    if "optimize_for" in payload: update["optimize_for"] = payload["optimize_for"]
    if not update:
        return {"ok": True}
    update["updated_at"] = supabase.functions.now()
    supabase.table("client_settings").upsert(
        {"client_id": ctx["client_id"], **update}, on_conflict="client_id"
    ).execute()
    return {"ok": True}

@router.put("/client/billing")
async def update_client_billing(
    payload: dict,
    supabase: Client = Depends(get_supabase),
    ident=Depends(maybe_get_identity),
    current_user=Depends(get_current_user),
):
    ctx = _resolve_client_ctx(supabase, ident, current_user)
    update = {k: v for k, v in payload.items() if k in ("billing_email","plan","monthly_quota","next_billing_date")}
    if not update:
        return {"ok": True}
    update["updated_at"] = supabase.functions.now()
    supabase.table("client_billing").upsert(
        {"client_id": ctx["client_id"], **update}, on_conflict="client_id"
    ).execute()
    return {"ok": True}

@router.get("/client/models")
async def list_client_models(
    supabase: Client = Depends(get_supabase),
    ident=Depends(maybe_get_identity),
    current_user=Depends(get_current_user),
):
    ctx = _resolve_client_ctx(supabase, ident, current_user)
    rows = (supabase.table("client_models")
            .select("model_key,display_name,is_active")
            .eq("client_id", ctx["client_id"])
            .execute().data) or []
    return rows
