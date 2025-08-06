# ==================== REQUEST SUBMISSION ====================

@app.post("/api/requests", response_model=RequestResponse)
async def create_request(
    request: RequestCreate,
    background_tasks: BackgroundTasks,
    current_user: Optional[Dict] = Depends(get_current_user),
    supabase: Client = Depends(get_db)
):
    """
    Main request submission endpoint - analyzes and determines execution path
    """
    try:
        # Determine user_id and priority
        if current_user:
            user_id = current_user["id"]
            priority = request.priority or current_user["default_priority"]
        else:
            # Create or get anonymous user
            anon_user = await get_or_create_anonymous_user(None, supabase)
            user_id = anon_user["id"]
            priority = request.priority or Priority.MEDIUM
        
        # Create request record with pending from fastapi import FastAPI, HTTPException, Depends, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import uuid

# Import your modules
from config import settings
from models import (
    RequestCreate, RequestResponse, RequestStatus, Priority,
    UserCreate, UserResponse, ApiKeyResponse,
    RequestDetail, ExecutionResult, RequestStatusUpdate,
    SystemStats, PriorityQueueStatus, UserUsageSummary,
    SystemConfig, SystemConfigResponse, ScheduleRequest,
    ThresholdResult
)
from auth import generate_api_key, hash_api_key, get_current_user, require_api_key

# Import your logic modules
from logic.predictor import Predictor
from logic.suggester import Suggester
from services.logger import RequestLogger
from services.scheduler import Scheduler
from services.threshold_checker import ThresholdChecker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
predictor = Predictor()
suggester = Suggester()
request_logger = RequestLogger()
scheduler = Scheduler()
threshold_checker = ThresholdChecker()

# Initialize Supabase client
def get_supabase() -> Client:
    """Create and return Supabase client instance"""
    return create_client(settings.supabase_url, settings.supabase_key)

# Dependency to get Supabase client with auth
def get_db(current_user: Optional[Dict] = Depends(get_current_user)) -> Client:
    """Dependency for database operations"""
    try:
        supabase = get_supabase()
        # Inject supabase into auth dependency
        if hasattr(get_current_user, '__wrapped__'):
            get_current_user.__wrapped__.__defaults__ = (supabase,)
        return supabase
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {str(e)}")
        raise HTTPException(status_code=503, detail="Database connection failed")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Taulayer AI Optimization API",
        "version": settings.api_version,
        "status": "active",
        "docs": "/docs"
    }

# Health check endpoint
@app.get("/health")
async def health_check(supabase: Client = Depends(get_db)):
    """Check API and database health"""
    try:
        # Test database connection
        result = supabase.table("users").select("count").limit(1).execute()
        return {
            "status": "healthy",
            "database": "connected",
            "api_version": settings.api_version,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "healthy",
            "database": "disconnected",
            "api_version": settings.api_version,
            "error": str(e)
        }

# ==================== USER MANAGEMENT ====================

@app.post("/api/users", response_model=UserResponse)
async def create_user(
    user: UserCreate,
    supabase: Client = Depends(get_db)
):
    """Create a new user"""
    try:
        result = supabase.table("users").insert({
            "provided_user_id": user.provided_user_id,
            "type": user.type,
            "default_priority": user.default_priority
        }).execute()
        
        if result.data:
            return UserResponse(**result.data[0])
        else:
            raise HTTPException(status_code=400, detail="Failed to create user")
    except Exception as e:
        logger.error(f"User creation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/users/{user_id}/api-key", response_model=ApiKeyResponse)
async def generate_user_api_key(
    user_id: str,
    supabase: Client = Depends(get_db)
):
    """Generate API key for a user"""
    try:
        # Generate new API key
        api_key = generate_api_key()
        api_key_hash = hash_api_key(api_key)
        
        # Update user with API key hash
        result = supabase.table("users").update({
            "api_key_hash": api_key_hash
        }).eq("id", user_id).execute()
        
        if result.data:
            return ApiKeyResponse(
                api_key=api_key,
                message="Save this API key securely. It cannot be retrieved again."
            )
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        logger.error(f"API key generation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/users/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Dict = Depends(require_api_key)
):
    """Get current user information"""
    return UserResponse(**current_user)

# ==================== PREDICTION API ====================

@app.post("/api/predict", response_model=PredictResponse)
async def predict_request(
    request: PredictRequest,
    current_user: Optional[Dict] = Depends(get_current_user),
    supabase: Client = Depends(get_db)
):
    """
    Main prediction endpoint - analyzes API request and returns optimization suggestions
    """
    try:
        # Determine user_id and priority
        if current_user:
            user_id = current_user["id"]
            priority = request.priority or current_user["default_priority"]
        else:
            # Create or get anonymous user
            anon_user = await get_or_create_anonymous_user(request.user_id, supabase)
            user_id = anon_user["id"]
            priority = request.priority or Priority.MEDIUM
        
        # Create request record
        request_data = {
            "user_id": user_id,
            "prompt": request.prompt,
            "status": RequestStatus.ANALYZING,
            "priority": priority
        }
        
        result = supabase.table("requests").insert(request_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create request")
        
        request_record = result.data[0]
        request_id = request_record["id"]
        
        try:
            # Perform predictions
            predictions = await predictor.analyze_request(request.prompt, request.metadata)
            
            # Generate suggestions
            suggestions = await suggester.generate_suggestions(predictions)
            
            # Update request with predictions
            update_data = {
                "predicted_latency": predictions.get("latency_ms"),
                "predicted_tokens": predictions.get("total_tokens"),
                "predicted_complexity": predictions.get("complexity_score"),
                "vector_embedding": predictions.get("embedding"),
                "reasoning": predictions.get("reasoning"),
                "suggestions": suggestions,
                "status": RequestStatus.COMPLETED,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            supabase.table("requests").update(update_data).eq("id", request_id).execute()
            
            # Log the request
            await request_logger.log_request(request_id, user_id, predictions, supabase)
            
            return PredictResponse(
                request_id=request_id,
                status=RequestStatus.COMPLETED,
                predictions=predictions,
                suggestions=suggestions,
                reasoning=predictions.get("reasoning", {})
            )
            
        except Exception as e:
            # Update request as failed
            supabase.table("requests").update({
                "status": RequestStatus.FAILED,
                "error_message": str(e),
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", request_id).execute()
            raise
            
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== REQUEST MANAGEMENT ====================

@app.get("/api/requests/{request_id}", response_model=RequestDetail)
async def get_request(
    request_id: str,
    current_user: Optional[Dict] = Depends(get_current_user),
    supabase: Client = Depends(get_db)
):
    """Get request details"""
    try:
        query = supabase.table("requests").select("*").eq("id", request_id)
        
        # If user is authenticated, ensure they own the request
        if current_user:
            query = query.eq("user_id", current_user["id"])
        
        result = query.single().execute()
        
        if result.data:
            return RequestDetail(**result.data)
        else:
            raise HTTPException(status_code=404, detail="Request not found")
    except Exception as e:
        logger.error(f"Get request error: {str(e)}")
        raise HTTPException(status_code=404, detail="Request not found")

@app.get("/api/requests", response_model=List[RequestDetail])
async def list_requests(
    status: Optional[RequestStatus] = Query(None),
    priority: Optional[Priority] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Optional[Dict] = Depends(get_current_user),
    supabase: Client = Depends(get_db)
):
    """List requests with optional filters"""
    try:
        query = supabase.table("requests").select("*")
        
        # Filter by user if authenticated
        if current_user:
            query = query.eq("user_id", current_user["id"])
        
        # Apply filters
        if status:
            query = query.eq("status", status)
        if priority:
            query = query.eq("priority", priority)
        
        # Order and paginate
        query = query.order("request_created_at", desc=True).range(offset, offset + limit - 1)
        
        result = query.execute()
        
        return [RequestDetail(**item) for item in result.data]
    except Exception as e:
        logger.error(f"List requests error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/requests/{request_id}/status", response_model=RequestDetail)
async def update_request_status(
    request_id: str,
    status_update: RequestStatusUpdate,
    current_user: Dict = Depends(require_api_key),
    supabase: Client = Depends(get_db)
):
    """Update request status (requires API key)"""
    try:
        update_data = {
            "status": status_update.status,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        if status_update.error_message:
            update_data["error_message"] = status_update.error_message
        
        result = supabase.table("requests").update(update_data).eq("id", request_id).eq("user_id", current_user["id"]).execute()
        
        if result.data:
            return RequestDetail(**result.data[0])
        else:
            raise HTTPException(status_code=404, detail="Request not found")
    except Exception as e:
        logger.error(f"Update status error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# ==================== EXECUTION RESULTS ====================

@app.post("/api/requests/{request_id}/execution", response_model=Dict[str, str])
async def report_execution_result(
    request_id: str,
    result: ExecutionResult,
    current_user: Dict = Depends(require_api_key),
    supabase: Client = Depends(get_db)
):
    """Report actual execution results for a request"""
    try:
        # Verify request exists and belongs to user
        request_check = supabase.table("requests").select("id").eq("id", request_id).eq("user_id", current_user["id"]).single().execute()
        
        if not request_check.data:
            raise HTTPException(status_code=404, detail="Request not found")
        
        # Update request executed_at
        supabase.table("requests").update({
            "executed_at": datetime.utcnow().isoformat(),
            "status": RequestStatus.COMPLETED
        }).eq("id", request_id).execute()
        
        # Insert into vector_index
        vector_data = {
            "requests_id": request_id,
            "actual_latency": result.actual_latency,
            "actual_token_usage": result.actual_token_usage,
            "actual_theoretical_complexity": result.actual_theoretical_complexity,
            "recommendations_for_improvement": result.recommendations_for_improvement,
            "executed_end": result.executed_end or datetime.utcnow().isoformat()
        }
        
        supabase.table("vector_index").insert(vector_data).execute()
        
        return {"message": "Execution results recorded successfully"}
    except Exception as e:
        logger.error(f"Execution result error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# ==================== ANALYTICS ====================

@app.get("/api/analytics/system-stats", response_model=SystemStats)
async def get_system_stats(
    supabase: Client = Depends(get_db)
):
    """Get system-wide statistics"""
    try:
        result = supabase.table("system_stats").select("*").execute()
        
        if result.data:
            return SystemStats(**result.data[0])
        else:
            # Return empty stats if view is empty
            return SystemStats(
                total_users=0,
                users_with_api_keys=0,
                total_requests=0,
                requests_last_hour=0,
                requests_last_24h=0,
                pending_requests=0,
                processing_requests=0,
                failed_requests=0,
                avg_predicted_latency=None,
                avg_actual_latency=None
            )
    except Exception as e:
        logger.error(f"System stats error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/queue-status", response_model=List[PriorityQueueStatus])
async def get_queue_status(
    supabase: Client = Depends(get_db)
):
    """Get priority queue status"""
    try:
        result = supabase.table("priority_queue_status").select("*").execute()
        return [PriorityQueueStatus(**item) for item in result.data]
    except Exception as e:
        logger.error(f"Queue status error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/user-usage", response_model=UserUsageSummary)
async def get_user_usage(
    current_user: Dict = Depends(require_api_key),
    supabase: Client = Depends(get_db)
):
    """Get usage statistics for current user"""
    try:
        result = supabase.table("user_usage_summary").select("*").eq("id", current_user["id"]).single().execute()
        
        if result.data:
            return UserUsageSummary(**result.data)
        else:
            raise HTTPException(status_code=404, detail="Usage data not found")
    except Exception as e:
        logger.error(f"User usage error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== SYSTEM CONFIGURATION ====================

@app.get("/api/config", response_model=List[SystemConfigResponse])
async def list_system_configs(
    current_user: Dict = Depends(require_api_key),
    supabase: Client = Depends(get_db)
):
    """List system configurations (requires API key)"""
    try:
        result = supabase.table("system_config").select("*").execute()
        return [SystemConfigResponse(**item) for item in result.data]
    except Exception as e:
        logger.error(f"List config error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/config", response_model=SystemConfigResponse)
async def create_system_config(
    config: SystemConfig,
    current_user: Dict = Depends(require_api_key),
    supabase: Client = Depends(get_db)
):
    """Create or update system configuration (requires API key)"""
    try:
        # Try to update existing config
        existing = supabase.table("system_config").select("id").eq("config_key", config.config_key).execute()
        
        if existing.data:
            # Update existing
            result = supabase.table("system_config").update({
                "config_value": config.config_value,
                "description": config.description,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("config_key", config.config_key).execute()
        else:
            # Create new
            result = supabase.table("system_config").insert({
                "config_key": config.config_key,
                "config_value": config.config_value,
                "description": config.description
            }).execute()
        
        if result.data:
            return SystemConfigResponse(**result.data[0])
        else:
            raise HTTPException(status_code=400, detail="Failed to save configuration")
    except Exception as e:
        logger.error(f"Save config error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# ==================== HELPER FUNCTIONS ====================

async def get_or_create_anonymous_user(provided_user_id: Optional[str], supabase: Client) -> Dict:
    """Get or create anonymous user"""
    if not provided_user_id:
        provided_user_id = f"anon_{uuid.uuid4().hex[:8]}"
    
    # Check if user exists
    result = supabase.table("users").select("*").eq("provided_user_id", provided_user_id).execute()
    
    if result.data:
        return result.data[0]
    else:
        # Create new anonymous user
        new_user = supabase.table("users").insert({
            "provided_user_id": provided_user_id,
            "type": "user prompt",
            "default_priority": "medium"
        }).execute()
        
        if new_user.data:
            return new_user.data[0]
        else:
            raise HTTPException(status_code=500, detail="Failed to create user")

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )