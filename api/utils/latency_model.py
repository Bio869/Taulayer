# api/utils/latency_model.py

def estimate_latency(prompt: str) -> int:
    """
    Dummy latency estimator. Returns fixed latency for now.
    """
    base_latency = 50  # ms
    length_factor = min(len(prompt) // 10, 50)  # scale with prompt length, capped
    return base_latency + length_factor
