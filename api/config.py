# api/config.py

from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv
import os

# Load .env if present
load_dotenv()

class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_key: str
    supabase_service_key: str = ""

    # API Info
    api_title: str = "Taulayer API"
    api_version: str = "1.0.0"
    api_description: str = "FastAPI backend with Supabase integration"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Other
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
