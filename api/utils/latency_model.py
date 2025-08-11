# api/utils/latency_model.py
def estimate_latency(prompt: str) -> int:
    """
    Simple latency model:
    base + min(chars/10, 50) + min(tokens-ish/5, 100)
    """
    base = 50  # ms
    length_factor = min(len(prompt) // 10, 50)
    tokenish = min(len(prompt) // 4 // 5, 100)  # rough second term
    return base + length_factor + tokenish
