# api/routes/client.py
from fastapi import APIRouter, Depends, HTTPException
from db.dependencies import get_supabase
from auth import get_current_user
from supabase import Client
from datetime import date

router = APIRouter()

@router.get("/client/me")
async def get_client_profile(supabase: Client = Depends(get_supabase), current_user=Depends(get_current_user)):
    client_id = (current_user or {}).get("client_id")
    if not client_id:
        raise HTTPException(status_code=404, detail="User has no client")

    # billing + settings
    billing = (supabase.table("client_billing").select("*").eq("client_id", client_id).single().execute().data) or {}
    settings = (supabase.table("client_settings").select("*").eq("client_id", client_id).single().execute().data) or {}

    # usage for this month
    month = date.today().replace(day=1).isoformat()
    usage = (supabase.table("client_usage_counters")
             .select("requests_count")
             .eq("client_id", client_id).eq("month", month).single().execute().data) or {"requests_count": 0}

    # models
    models = (supabase.table("client_models").select("model_key,display_name,is_active")
              .eq("client_id", client_id).eq("is_active", True).execute().data) or []

    return {
        "client_id": client_id,
        "billing": billing,
        "settings": settings,
        "usage": {"month": month, "requests_this_month": usage.get("requests_count", 0)},
        "models": models,
    }

@router.put("/client/settings")
async def update_client_settings(payload: dict, supabase: Client = Depends(get_supabase), current_user=Depends(get_current_user)):
    client_id = (current_user or {}).get("client_id")
    if not client_id:
        raise HTTPException(status_code=404, detail="User has no client")

    update = {}
    if "config_yaml" in payload:   update["config_yaml"] = payload["config_yaml"]
    if "optimize_for" in payload:  update["optimize_for"] = payload["optimize_for"]
    if not update: return {"ok": True}

    update["updated_at"] = supabase.functions.now()
    supabase.table("client_settings").upsert({"client_id": client_id, **update}, on_conflict="client_id").execute()
    return {"ok": True}

@router.put("/client/billing")
async def update_client_billing(payload: dict, supabase: Client = Depends(get_supabase), current_user=Depends(get_current_user)):
    client_id = (current_user or {}).get("client_id")
    if not client_id:
        raise HTTPException(status_code=404, detail="User has no client")

    update = {}
    for k in ("billing_email","plan","monthly_quota","next_billing_date"):
        if k in payload: update[k] = payload[k]
    if not update: return {"ok": True}

    update["updated_at"] = supabase.functions.now()
    supabase.table("client_billing").upsert({"client_id": client_id, **update}, on_conflict="client_id").execute()
    return {"ok": True}

@router.get("/client/models")
async def list_client_models(supabase: Client = Depends(get_supabase), current_user=Depends(get_current_user)):
    client_id = (current_user or {}).get("client_id")
    if not client_id:
        raise HTTPException(status_code=404, detail="User has no client")
    rows = supabase.table("client_models").select("model_key,display_name,is_active").eq("client_id", client_id).execute().data or []
    return rows
