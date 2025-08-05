from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

# Enums matching your database
class RequestStatus(str, Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class UserType(str, Enum):
    USER_PROMPT = "user prompt"
    AGENT_PROMPT = "agent prompt"
    OTHER = "other"

# Request Models
class PredictRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="The API request prompt to analyze")
    user_id: Optional[str] = Field(None, description="Optional user identifier")
    priority: Optional[Priority] = Field(None, description="Request priority override")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

class PredictResponse(BaseModel):
    request_id: uuid.UUID
    status: RequestStatus
    predictions: Dict[str, Any] = Field(..., description="Latency, token, and complexity predictions")
    suggestions: List[Dict[str, Any]] = Field(default_factory=list, description="Optimization suggestions")
    reasoning: Dict[str, Any] = Field(default_factory=dict, description="Prediction reasoning")

# User Models
class UserCreate(BaseModel):
    provided_user_id: str = Field(..., min_length=1, max_length=255)
    type: UserType = UserType.USER_PROMPT
    default_priority: Priority = Priority.MEDIUM

class UserResponse(BaseModel):
    id: uuid.UUID
    provided_user_id: str
    type: UserType
    default_priority: Priority
    created_at: datetime
    has_api_key: bool = False

class ApiKeyResponse(BaseModel):
    api_key: str
    message: str

# Request Status Models
class RequestStatusUpdate(BaseModel):
    status: RequestStatus
    error_message: Optional[str] = None

class RequestDetail(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    prompt: str
    status: RequestStatus
    priority: Priority
    predicted_latency: Optional[int] = None
    predicted_tokens: Optional[int] = None
    predicted_complexity: Optional[float] = None
    reasoning: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[Dict[str, Any]]] = None
    request_created_at: datetime
    updated_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    error_message: Optional[str] = None

# Execution Result Models
class ExecutionResult(BaseModel):
    request_id: uuid.UUID
    actual_latency: int = Field(..., description="Actual latency in milliseconds")
    actual_token_usage: int = Field(..., description="Actual tokens used")
    actual_theoretical_complexity: Optional[float] = None
    recommendations_for_improvement: Optional[List[Dict[str, Any]]] = None
    executed_end: Optional[datetime] = None

# Analytics Models
class SystemStats(BaseModel):
    total_users: int
    users_with_api_keys: int
    total_requests: int
    requests_last_hour: int
    requests_last_24h: int
    pending_requests: int
    processing_requests: int
    failed_requests: int
    avg_predicted_latency: Optional[float]
    avg_actual_latency: Optional[float]

class PriorityQueueStatus(BaseModel):
    priority: Priority
    queue_count: int
    processing_count: int
    avg_predicted_latency: Optional[float]
    oldest_request: Optional[datetime]
    newest_request: Optional[datetime]

class UserUsageSummary(BaseModel):
    id: uuid.UUID
    provided_user_id: str
    type: UserType
    has_api_key: bool
    total_requests: int
    requests_last_hour: int
    requests_last_24h: int
    failed_requests: int
    completed_requests: int
    avg_actual_latency: Optional[float]
    last_request_at: Optional[datetime]

# System Config Models
class SystemConfig(BaseModel):
    config_key: str
    config_value: Dict[str, Any]
    description: Optional[str] = None

class SystemConfigResponse(SystemConfig):
    id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime]