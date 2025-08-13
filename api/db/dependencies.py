# api/db/dependencies.py
from functools import lru_cache
import logging
from supabase import create_client, Client
from config import settings

logger = logging.getLogger(__name__)

@lru_cache()
def get_supabase() -> Client:
    """
    Singleton Supabase client.
    Prefers SUPABASE_SERVICE_KEY so the API can bypass RLS.
    """
    url = settings.supabase_url
    key = settings.supabase_service_key or settings.supabase_key

    if not url:
        raise RuntimeError("SUPABASE_URL is not configured")
    if not key:
        raise RuntimeError("Neither SUPABASE_SERVICE_KEY nor SUPABASE_KEY is configured")

    if not settings.supabase_service_key:
        logger.warning(
            "Supabase service key not set; falling back to public key. "
            "RLS-protected operations may fail. Set SUPABASE_SERVICE_KEY."
        )

    # One client per process; HTTP keep-alive reused across requests
    return create_client(url, key)

# Handy for tests / key rotation without a restart
def _reset_supabase_client_cache() -> None:
    try:
        get_supabase.cache_clear()  # type: ignore[attr-defined]
    except Exception:
        pass
