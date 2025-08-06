from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    # Supabase settings
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_key: str = os.getenv("SUPABASE_KEY", "")
    supabase_service_key: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    
    # API settings
    api_title: str = "Taulayer API"
    api_version: str = "1.0.0"
    api_description: str = "FastAPI backend with Supabase integration"
    
    # CORS settings
    cors_origins: list = ["http://localhost:3000", "http://localhost:8000"]
    
    # Other settings
    debug: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings():
    return Settings()

# Create settings instance
settings = get_settings()