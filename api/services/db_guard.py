# api/services/db_guard.py
import time
from typing import Callable, TypeVar
from fastapi import HTTPException
import logging
from config import settings

# Supabase uses httpx/httpcore underneath; catch both.
try:
    import httpx
    import httpcore
except Exception:  # pragma: no cover (if libs change)
    httpx = None
    httpcore = None

T = TypeVar("T")
logger = logging.getLogger(__name__)

RETRYABLE_EXC = tuple(filter(None, [
    getattr(httpx, "ReadTimeout", None),
    getattr(httpx, "ConnectTimeout", None),
    getattr(httpx, "PoolTimeout", None),
    getattr(httpx, "WriteError", None),
    getattr(httpx, "NetworkError", None),
    getattr(httpcore, "ReadTimeout", None),
    getattr(httpcore, "ConnectTimeout", None),
    getattr(httpcore, "WriteError", None),
    getattr(httpcore, "NetworkError", None),
    ConnectionError,
    TimeoutError,
]))

def classify_and_raise(e: Exception) -> None:
    """
    Translate low-level network/db exceptions into appropriate HTTP errors:
      - Timeout -> 504
      - Connect/Network/DNS -> 503
      - Other unexpected -> 500
    """
    msg = str(e)
    # Timeouts
    if any(name in type(e).__name__.lower() for name in ["timeout"]) or "timeout" in msg.lower():
        raise HTTPException(status_code=504, detail="Upstream database timeout")
    # Network/connectivity
    raise HTTPException(status_code=503, detail="Database temporarily unavailable")

def with_retry(fn: Callable[[], T], *, attempts=settings.db_retry_attempts, backoff_ms=settings.db_retry_backoff_ms) -> T:
    """
    Execute `fn()` with simple exponential backoff on known transient errors.
    attempts=3 → delays: 0ms, 150ms, 300ms (total ~450ms)
    """
    last_err = None
    for i in range(attempts):
        try:
            return fn()
        except RETRYABLE_EXC as e:  # transient
            last_err = e
            if i < attempts - 1:
                time.sleep(backoff_ms / 1000.0 * (2 ** i))
                continue
            logger.warning("DB transient error after retries: %s", e)
            classify_and_raise(e)
        except Exception as e:  # non-transient or postgrest errors
            last_err = e
            break
    # Non-transient or unknown errors → map conservatively
    classify_and_raise(last_err or Exception("Unknown DB error"))
