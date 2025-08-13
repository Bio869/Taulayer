# api/services/executor.py
from datetime import datetime, timezone
from api.db.dependencies import get_supabase
from api.services.logger import log

async def execute_request_job(request_id: str):
    sb = get_supabase()

    # 1. Fetch request info and user email
    req = sb.table("requests").select("prompt,user_id").eq("id", request_id).single().execute().data
    user = sb.table("users").select("email").eq("id", req["user_id"]).single().execute().data
    email_to = user.get("email")

    prompt = req["prompt"]

    # 2. Run the model / heavy logic
    result = {
        "answer": f"Echo: {prompt}",
        "embedding": [0.01, 0.02],
        "latency_ms": 1200,
        "tokens_used": 250,
        "reasoning_summary": "Execution complete",
    }

    # 3. Save results to vector_index
    sb.table("vector_index").insert({
        "requests_id": request_id,
        "vector_embedding": result["embedding"],
        "executed_end": datetime.now(timezone.utc).isoformat(),
        "actual_latency": result["latency_ms"],
        "actual_token_usage": result["tokens_used"],
        "reasoning_summary": result["reasoning_summary"],
        "answer": result["answer"],
    }).execute()

    # 4. Mark request as completed
    sb.table("requests").update({
        "status": "completed",
        "executed_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", request_id).execute()

    log.info("Executed job", extra={"request_id": request_id})

    # 5. Send email notification
    if email_to:
        send_email_notification(email_to, request_id)

def send_email_notification(to_email: str, request_id: str):
    # Example using a simple print; replace with your email service
    log.info("Sending email", extra={"to": to_email, "request_id": request_id})
    # Here you’d integrate with Postmark, SendGrid, SES, etc.
