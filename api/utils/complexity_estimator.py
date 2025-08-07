# api/utils/complexity_estimator.py

def estimate_complexity(prompt: str) -> float:
    """
    Stub complexity scorer.
    Returns a value between 0.0 and 1.0 based on naive prompt length scaling.
    """
    length = len(prompt)
    # Simple scaling: 0 to 1.0 based on length capped at 1000 chars
    return min(length / 1000.0, 1.0)
