# api/services/logger.py

import logging
from datetime import datetime
from typing import Dict

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


def log_event(event_type: str, request_id: str, details: Dict = {}):
    """
    Log an event with its type, request ID, timestamp, and optional details.
    """
    log_entry = {
        "event_type": event_type,
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat(),
        "details": details
    }
    logger.info(f"[EVENT] {log_entry}")
