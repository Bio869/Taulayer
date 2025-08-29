# api/schemas.py
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, List, Literal, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, ConfigDict

# ──────────────────────────────────────────────────────────────────────────────
# Type aliases / enums
# ──────────────────────────────────────────────────────────────────────────────

Priority = Literal["low", "medium", "high"]

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

# ──────────────────────────────────────────────────────────────────────────────
# Utilities
# ──────────────────────────────────────────────────────────────────────────────

def _to_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Coerce datetimes to timezone-aware UTC; pass through None."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

# ──────────────────────────────────────────────────────────────────────────────
# Suggestion object (rich shape for POST responses)
# ──────────────────────────────────────────────────────────────────────────────

class Suggestion(BaseModel):
    title: str
    description: str
    impact: Optional[str] = None
    priority: Optional[int] = None
    implementation_effort: Optional[str] = None

    model_config = ConfigDict(extra="ignore")

# ──────────────────────────────────────────────────────────────────────────────
# Incoming payload (POST /requests)
# ──────────────────────────────────────────────────────────────────────────────

class RequestCreate(BaseModel):
    """
    Payload for POST /requests.
    - 'scheduled_for' is preferred; legacy alias 'schedule_at' is also accepted.
    """
    prompt: str
    priority: Optional[Priority] = "medium"
    scheduled_for: Optional[datetime] = Field(
        default=None,
        description="UTC time to run later",
        alias="schedule_at",
    )
    metadata: Optional[Dict[str, Any]] = None
    user_id: Optional[UUID] = None

    model_config = ConfigDict(
        populate_by_name=True,  # allow using either 'scheduled_for' or alias 'schedule_at'
        extra="ignore",
    )

    @field_validator("scheduled_for", mode="before")
    @classmethod
    def _parse_and_normalize_scheduled_for(cls, v):
        # Accept str/isoformat or datetime; normalize to UTC if provided.
        if v is None:
            return v
        if isinstance(v, str):
            try:
                parsed = datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                raise ValueError("scheduled_for must be ISO-8601 datetime (e.g., 2025-08-13T19:00:00Z)")
            return _to_utc(parsed)
        if isinstance(v, datetime):
            return _to_utc(v)
        raise ValueError("scheduled_for must be a datetime or ISO-8601 string")

# ──────────────────────────────────────────────────────────────────────────────
# Response after creation/analysis (POST /requests)
# ──────────────────────────────────────────────────────────────────────────────

class RequestResponse(BaseModel):
    request_id: str
    status: RequestStatus
    latency_estimate: Optional[int] = None
    token_estimate: Optional[int] = None
    complexity_score: Optional[float] = None
    estimated_completion_time: Optional[datetime] = None
    # For POST responses we build rich Suggestion objects
    suggestions: Optional[List[Suggestion]] = None

    model_config = ConfigDict(extra="ignore")

# ──────────────────────────────────────────────────────────────────────────────
# Authenticated User Schema
# ──────────────────────────────────────────────────────────────────────────────

class UserSchema(BaseModel):
    id: str
    type: Literal["user prompt", "agent prompt", "other"]
    default_priority: Priority

    # DB column is provided_user_id; accept 'external_id' as an alias for input only
    provided_user_id: str = Field(..., alias="external_id")

    # New, optional tenancy & access controls
    client_name: Optional[str] = None         # <-- newly added column

    api_key_hash: Optional[str] = None        # not returned in responses
    created_at: datetime

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,  # honor the alias for inbound payloads
    )


# Optional: a trimmed response shape for the frontend (no sensitive fields)
class UserPublic(BaseModel):
    id: str
    email: Optional[str] = None
    client_name: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(extra="ignore")

# ──────────────────────────────────────────────────────────────────────────────
# Full request detail (e.g., GET /api/requests/{id})
# ──────────────────────────────────────────────────────────────────────────────

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

    # Embedding snapshot at analysis time (if you store it here)
    vector_embedding: Optional[List[float]] = None

    # In DB this is JSONB (array). We surface as List[str] on GET.
    suggestions: Optional[List[str]] = None

    # Execution scheduling
    scheduled_for: Optional[datetime] = None

    # Per-request notify email (nullable)
    notify_email: Optional[str] = None

    # Any error or note during analysis/execution
    request_note: Optional[str] = None

    # Lifecycle timestamps
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(extra="ignore")

    @field_validator("scheduled_for", mode="before")
    @classmethod
    def _normalize_detail_scheduled_for(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            try:
                parsed = datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                # If it's coming from DB already in another string format, pass through
                return v
            return _to_utc(parsed)
        if isinstance(v, datetime):
            return _to_utc(v)
        return v
