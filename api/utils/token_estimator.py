# api/utils/token_estimator.py
"""
Lightweight token estimator.

- Tries tiktoken (cl100k_base) if available.
- Falls back to a ~4 chars/token heuristic.
"""
from __future__ import annotations

_enc = None
try:
    import tiktoken
    _enc = tiktoken.get_encoding("cl100k_base")
except Exception:
    _enc = None

def estimate_tokens(prompt: str) -> int:
    if not prompt:
        return 0
    if _enc:
        try:
            return len(_enc.encode(prompt))
        except Exception:
            pass
    # simple fallback
    return (len(prompt) + 3) // 4
