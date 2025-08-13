# api/config.py
from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Supabase ───────────────────────────────────────────────────────────────
    supabase_url: str = Field(..., alias="SUPABASE_URL")
    supabase_key: Optional[str] = Field(default=None, alias="SUPABASE_KEY")
    supabase_service_key: Optional[str] = Field(default=None, alias="SUPABASE_SERVICE_KEY")

    # ── Prompt guards ──────────────────────────────────────────────────────────
    prompt_max_chars: int = Field(default=4000, alias="PROMPT_MAX_CHARS")
    prompt_min_chars: int = Field(default=1, alias="PROMPT_MIN_CHARS")

    # ── API Info ───────────────────────────────────────────────────────────────
    api_title: str = Field(default="TauLayer API", alias="API_TITLE")
    api_version: str = Field(default="1.0.0", alias="API_VERSION")
    api_description: str = Field(default="FastAPI backend with Supabase integration", alias="API_DESCRIPTION")

    # ── CORS ───────────────────────────────────────────────────────────────────
    # Comma-separated env: CORS_ORIGINS="http://localhost:3000,http://localhost:8000"
    cors_origins: List[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:8000"],
        alias="CORS_ORIGINS",
    )

    # ── Debug / retries ────────────────────────────────────────────────────────
    debug: bool = Field(default=True, alias="DEBUG")
    db_retry_attempts: int = Field(default=3, alias="DB_RETRY_ATTEMPTS")
    db_retry_backoff_ms: int = Field(default=150, alias="DB_RETRY_BACKOFF_MS")

    # ── Background / worker knobs ──────────────────────────────────────────────
    # If true, start the durable worker loop on app startup
    run_worker: bool = Field(default=False, alias="RUN_WORKER")

    # For deciding whether to use BackgroundTasks vs durable queue
    background_max_latency_ms: int = Field(default=2000, alias="BACKGROUND_MAX_LATENCY_MS")

    # Durable jobs queue configuration
    queue_max_attempts: int = Field(default=5, alias="QUEUE_MAX_ATTEMPTS")
    queue_batch_size: int = Field(default=10, alias="QUEUE_BATCH_SIZE")
    queue_lock_ttl_sec: int = Field(default=120, alias="QUEUE_LOCK_TTL_SEC")
    queue_backoff_base_sec: int = Field(default=15, alias="QUEUE_BACKOFF_BASE_SEC")
    queue_backoff_cap_sec: int = Field(default=600, alias="QUEUE_BACKOFF_CAP_SEC")

    # ── Pydantic Settings config ───────────────────────────────────────────────
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,  # allow aliases to populate fields
    )

    # ── Validators ─────────────────────────────────────────────────────────────
    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors_origins(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            # split comma-separated list, strip spaces
            return [s.strip() for s in v.split(",") if s.strip()]
        if isinstance(v, (list, tuple)):
            return list(v)
        raise ValueError("CORS_ORIGINS must be a comma-separated string or a list")

    @field_validator("supabase_key", "supabase_service_key", mode="before")
    @classmethod
    def _empty_str_to_none(cls, v):
        # Treat empty strings as None for optional keys
        if isinstance(v, str) and v.strip() == "":
            return None
        return v

    @model_validator(mode="after")
    def _require_some_supabase_key(self):
        # Ensure at least one of the keys is present
        if not (self.supabase_service_key or self.supabase_key):
            raise ValueError("Either SUPABASE_SERVICE_KEY or SUPABASE_KEY must be set")
        return self


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
