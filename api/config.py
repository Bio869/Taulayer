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
    prompt_max_chars: int = int(os.getenv("PROMPT_MAX_CHARS", "4000"))
    prompt_min_chars: int = int(os.getenv("PROMPT_MIN_CHARS", "1"))

    # API Info
    api_title: str = "Taulayer API"
    api_version: str = "1.0.0"
    api_description: str = "FastAPI backend with Supabase integration"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Other
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    db_retry_attempts: int = int(os.getenv("DB_RETRY_ATTEMPTS", "3"))
    db_retry_backoff_ms: int = int(os.getenv("DB_RETRY_BACKOFF_MS", "150"))

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
