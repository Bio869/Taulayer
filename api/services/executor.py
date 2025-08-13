# api/services/executor.py
from datetime import datetime, timezone
from typing import Optional

from db.dependencies import get_supabase
from services.logger import log

async def execute_request_job(request_id: str):
    sb = get_supabase()

    # 1) Fetch request info (prompt + user_id)
    req = sb.table("requests").select("prompt,user_id").eq("id", request_id).single().execute().data
    if not req:
        log.error("Request not found", extra={"request_id": request_id})
        return

    prompt = req["prompt"]
    user_id = req["user_id"]

    # 2) (Optional) fetch user email; may be NULL
    email_to: Optional[str] = None
    try:
        user = sb.table("users").select("email").eq("id", user_id).single().execute().data
        if user:
            email_to = user.get("email")  # may be None
    except Exception:
        # If users.email doesn't exist or query fails, just continue without email
        log.warning("Could not fetch user email", extra={"user_id": user_id})

    # 3) Run your heavy logic / LLM flow (placeholder)
    result = {
        "answer": f"Echo: {prompt[:400]}",
        "embedding": [0.01, 0.02],     # provider payload or vector
        "latency_ms": 1200,
        "tokens_used": 250,
        "reasoning_summary": "Execution completed",
    }

    # 4) Save results to vector_index
    sb.table("vector_index").insert({
        "requests_id": request_id,
        "vector_embedding": result["embedding"],
        "executed_end": datetime.now(timezone.utc).isoformat(),
        "actual_latency": result["latency_ms"],
        "actual_token_usage": result["tokens_used"],
        "reasoning_summary": result["reasoning_summary"],
        "answer": result["answer"],
    }).execute()

    # 5) Mark the request as completed
    sb.table("requests").update({
        "status": "completed",
        "executed_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", request_id).execute()

    log.info("Executed job", extra={"request_id": request_id})

    # 6) Notify (only if we actually have an email)
    if email_to:
        # A) Direct send (plug your provider here), OR
        # B) Outbox pattern (recommended for reliability). Example B shown:
        try:
            sb.table("notification_outbox").insert({
                "request_id": request_id,
                "channel": "email",
                "recipient": email_to,
                "payload": {
                    "subject": "Your TauLayer result is ready",
                    "request_id": request_id,
                },
            }).execute()
            log.info("Queued email notification", extra={"to": email_to, "request_id": request_id})
        except Exception as e:
            log.warning("Failed to queue email notification", extra={"error": str(e), "to": email_to})
    else:
        log.info("No email on file; skipping notification", extra={"user_id": user_id})
