# api/workflow_requests.py

from fastapi import APIRouter, Depends, BackgroundTasks
from datetime import datetime, timedelta
from typing import Optional, Dict
from auth import get_or_create_anonymous_user
from supabase import Client
from schemas import RequestCreate, RequestResponse, Priority, Suggestion
from config import settings
from auth import get_current_user
from services import request_handler, scheduler
from logic import predictor, suggester
from db.dependencies import get_db

router = APIRouter()

@router.post("/requests", response_model=RequestResponse)
async def create_request(
    request: RequestCreate,
    background_tasks: BackgroundTasks,
    current_user: Optional[Dict] = Depends(get_current_user),
    supabase: Client = Depends(get_db)
):
    # 1. Determine user identity
    user_id = current_user["id"] if current_user else get_or_create_anonymous_user(supabase)["id"]
    priority = request.priority or (current_user.get("default_priority") if current_user else "medium")

    # 2. Create request row (PENDING → ANALYZING)
    request_id = request_handler.create_request(supabase, user_id, request.prompt, priority)

    # 3. Synchronous prediction
    predictions = predictor.analyze_request(request.prompt)

    # 4. Threshold evaluation
    result = predictor.check_thresholds(predictions, priority)

    now = datetime.utcnow()

    if result.passed:
        # Update request and queue async execution
        request_handler.update_after_analysis(supabase, request_id, predictions, "sent_to_execution")

        def dummy_llm_execution():
            import time, json
            time.sleep(1)  # Simulate delay
            with open("llm_fixed_answer.json") as f:
                metrics = json.load(f)
            metrics["executed_end"] = datetime.utcnow().isoformat()
            request_handler.finalize_execution(supabase, request_id, metrics, success=True)

        scheduler.enqueue_background_task(background_tasks, dummy_llm_execution)

        return RequestResponse(
            request_id=request_id,
            status="sent_to_execution",
            latency_estimate=predictions["latency_ms"],
            token_estimate=predictions["total_tokens"],
            complexity_score=predictions["complexity_score"],
            estimated_completion_time=now + timedelta(milliseconds=predictions["latency_ms"] + 300)
        )

    else:
        # Failed threshold → generate suggestions
        tips = suggester.generate_suggestions(request.prompt)
        request_handler.update_after_analysis(supabase, request_id, predictions, "below_threshold_suggestions_sent")

        suggestion_objs = [
            Suggestion(title=tip, description=tip) for tip in tips
        ]

        return RequestResponse(
            request_id=request_id,
            status="below_threshold_suggestions_sent",
            latency_estimate=predictions["latency_ms"],
            token_estimate=predictions["total_tokens"],
            complexity_score=predictions["complexity_score"],
            suggestions=suggestion_objs
        )
print("✅ workflow_requests router successfully loaded")
