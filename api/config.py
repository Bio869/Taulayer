from pydantic import BaseSettings  # Not from pydantic_settings
from functools import lru_cache
from typing import List

class Settings(BaseSettings):
    # Supabase settings
    supabase_url: str
    supabase_key: str
    supabase_service_key: str
    
    # API settings
    api_title: str = "Taulayer API"
    api_version: str = "1.0.0"
    api_description: str = "FastAPI backend with Supabase integration"
    
    # CORS settings
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
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