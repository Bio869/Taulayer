from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from typing import List, Dict, Any
import logging

# Import your configurations
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase client
def get_supabase() -> Client:
    """Create and return Supabase client instance"""
    return create_client(settings.supabase_url, settings.supabase_key)

# Dependency to get Supabase client
def get_db() -> Client:
    """Dependency for database operations"""
    try:
        return get_supabase()
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {str(e)}")
        raise HTTPException(status_code=503, detail="Database connection failed")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Taulayer API",
        "version": settings.api_version,
        "status": "active"
    }

# Health check endpoint
@app.get("/health")
async def health_check(supabase: Client = Depends(get_db)):
    """Check API and database health"""
    try:
        # Test database connection
        # You can modify this based on your table structure
        result = supabase.table("_test").select("*").limit(1).execute()
        return {
            "status": "healthy",
            "database": "connected",
            "api_version": settings.api_version
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "healthy",
            "database": "disconnected",
            "api_version": settings.api_version,
            "note": "Database test query failed, but API is running"
        }

# Example: User registration endpoint
@app.post("/auth/register")
async def register(email: str, password: str, supabase: Client = Depends(get_db)):
    """Register a new user"""
    try:
        # Supabase auth sign up
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if response.user:
            return {
                "message": "User registered successfully",
                "user_id": response.user.id,
                "email": response.user.email
            }
        else:
            raise HTTPException(status_code=400, detail="Registration failed")
            
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# Example: User login endpoint
@app.post("/auth/login")
async def login(email: str, password: str, supabase: Client = Depends(get_db)):
    """Login user"""
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.user:
            return {
                "message": "Login successful",
                "user_id": response.user.id,
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

# Example: Get user profile (protected endpoint)
@app.get("/auth/profile")
async def get_profile(authorization: str, supabase: Client = Depends(get_db)):
    """Get user profile - requires authentication"""
    try:
        # Set the auth header
        supabase.auth.set_session(authorization)
        
        # Get the current user
        user = supabase.auth.get_user()
        
        if user:
            return {
                "user_id": user.user.id,
                "email": user.user.email,
                "created_at": user.user.created_at
            }
        else:
            raise HTTPException(status_code=401, detail="Not authenticated")
            
    except Exception as e:
        logger.error(f"Profile fetch error: {str(e)}")
        raise HTTPException(status_code=401, detail="Not authenticated")

# Example: CRUD operations for a sample table
# Let's assume you have a 'tasks' table in Supabase

@app.get("/tasks", response_model=List[Dict[str, Any]])
async def get_tasks(supabase: Client = Depends(get_db)):
    """Get all tasks"""
    try:
        response = supabase.table("tasks").select("*").execute()
        return response.data
    except Exception as e:
        logger.error(f"Error fetching tasks: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch tasks")

@app.post("/tasks")
async def create_task(title: str, description: str = None, supabase: Client = Depends(get_db)):
    """Create a new task"""
    try:
        data = {
            "title": title,
            "description": description,
            "completed": False
        }
        response = supabase.table("tasks").insert(data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Error creating task: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create task")

@app.put("/tasks/{task_id}")
async def update_task(task_id: int, completed: bool, supabase: Client = Depends(get_db)):
    """Update task status"""
    try:
        response = supabase.table("tasks").update(
            {"completed": completed}
        ).eq("id", task_id).execute()
        
        if response.data:
            return response.data[0]
        else:
            raise HTTPException(status_code=404, detail="Task not found")
    except Exception as e:
        logger.error(f"Error updating task: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update task")

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int, supabase: Client = Depends(get_db)):
    """Delete a task"""
    try:
        response = supabase.table("tasks").delete().eq("id", task_id).execute()
        return {"message": "Task deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting task: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete task")

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )