# api/services/logger.py

import logging
from datetime import datetime
from typing import Dict, Optional

# Create logger for the current module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Add handler if not already added (avoid duplicate handlers in reloads)
if not logger.handlers:
    handler = logging.StreamHandler()  # Logs to stdout
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def log_event(event_type: str, request_id: Optional[str] = None, details: Dict = {}):
    """
    Log an event with its type, optional request ID, timestamp, and details.
    Examples:
        log_event("request_created", request_id="abc123", details={"priority": "high"})
        log_event("unauthorized_access", details={"source_ip": "1.2.3.4"})
    """
    log_entry = {
        "event_type": event_type,
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat(),
        "details": details or {}
    }
    logger.info(f"[EVENT] {log_entry}")


def log_unauthorized_access(reason: str, extra: Dict = {}):
    """
    Special helper for logging unverified/unauthorized API access attempts.
    These won't be persisted in DB but should be visible in logs.
    """
    details = {"reason": reason}
    if extra:
        details.update(extra)

    log_event("unauthorized_access", request_id=None, details=details)
