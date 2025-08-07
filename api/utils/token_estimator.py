# api/utils/token_estimator.py

def estimate_tokens(prompt: str) -> int:
    """
    Estimates *output* token count. For now, return a fixed value.
    Advanced versions may include cached or reasoning tokens.
    """
    return 150  # fixed stub for output token count
