# api/schemas.py

from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict, Any
from datetime import datetime

# Priority levels
Priority = Literal["low", "medium", "high"]

# Request statuses
RequestStatus = Literal[
    "pending",
    "analyzing",
    "sent_to_execution",
    "processing",
    "completed",
    "failed",
    "cancelled",
    "below_threshold_suggestions_sent",
]

# A single suggestion object
class Suggestion(BaseModel):
    title: str
    description: str
    impact: Optional[str] = None
    priority: Optional[int] = None
    implementation_effort: Optional[str] = None

# ─── Incoming payload ────────────────────────────────────────────────────────────
class RequestCreate(BaseModel):
    prompt: str
    priority: Optional[Priority] = "medium"
    scheduled_for: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

# ─── Response after creation/analysis ────────────────────────────────────────────
class RequestResponse(BaseModel):
    request_id: str
    status: RequestStatus
    latency_estimate: Optional[int] = None
    token_estimate: Optional[int] = None
    complexity_score: Optional[float] = None
    estimated_completion_time: Optional[datetime] = None
    suggestions: Optional[List[Suggestion]] = None

# ─── Authenticated User Schema ────────────────────────────────────────────────
class UserSchema(BaseModel):
    id: str
    type: Literal["user prompt", "agent prompt"]
    default_priority: Priority
    provided_user_id: str
    api_key_hash: Optional[str] = None  # Not returned in responses, only used for lookup
    created_at: datetime

# ─── Full request detail (e.g. GET /api/requests/{id}) ─────────────────────────
class RequestDetail(BaseModel):
    id: str
    user_id: str
    prompt: str
    status: RequestStatus
    priority: Priority

    # Predictions (from analysis)
    predicted_latency: Optional[int] = None
    predicted_tokens: Optional[int] = None
    predicted_complexity: Optional[float] = None

    # Embedding stored at analysis time
    vector_embedding: Optional[List[float]] = None

    # Internal reasoning string
    reasoning: Optional[str] = None

    # If thresholds failed, a list of actionable suggestions
    suggestions: Optional[List[Suggestion]] = None

    # Execution scheduling
    scheduled_for: Optional[datetime] = None

    # Any error during analysis or execution
    error_message: Optional[str] = None

    # Lifecycle timestamps
    created_at: datetime
    updated_at: datetime
