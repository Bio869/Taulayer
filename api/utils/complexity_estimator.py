# api/utils/complexity_estimator.py
def estimate_complexity(prompt: str) -> float:
    """
    Naive complexity: mostly length-driven with a tiny structure boost.
    """
    length = len(prompt)
    base = min(length / 1000.0, 1.0)
    has_list = ("bullet" in prompt.lower()) or ("1." in prompt) or ("- " in prompt)
    has_analytics_words = any(w in prompt.lower() for w in ["compare", "forecast", "rank", "anomal", "segment"])
    bump = 0.05 * sum([has_list, has_analytics_words])
    return min(base + bump, 1.0)
