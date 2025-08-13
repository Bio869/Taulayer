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
    Falls back to SUPABASE_KEY if the service key is not set.
    """
    url: str = settings.supabase_url
    service_key: str | None = settings.supabase_service_key
    public_key: str | None = settings.supabase_key

    if not url:
        raise RuntimeError("SUPABASE_URL is not configured")
    if not (service_key or public_key):
        raise RuntimeError("Neither SUPABASE_SERVICE_KEY nor SUPABASE_KEY is configured")

    if service_key:
        key_to_use = service_key
        logger.debug("Using Supabase service key (bypasses RLS)")
    else:
        key_to_use = public_key
        logger.warning(
            "Supabase service key not set; using public key. "
            "RLS-protected operations may fail. "
            "Set SUPABASE_SERVICE_KEY for full server-side access."
        )

    # One client per process; HTTP keep-alive reused across requests
    return create_client(url, key_to_use)


def _reset_supabase_client_cache() -> None:
    """
    Clears the cached Supabase client instance.
    Useful for tests or when rotating API keys without restarting the process.
    """
    try:
        get_supabase.cache_clear()  # type: ignore[attr-defined]
        logger.debug("Supabase client cache cleared")
    except Exception as e:
        logger.exception("Error clearing Supabase client cache: %s", e)
