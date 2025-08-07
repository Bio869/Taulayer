# api/services/threshold_checker.py

from typing import Dict, List
from pydantic import BaseModel

class ThresholdResult(BaseModel):
    passed: bool
    failed_reasons: List[str] = []

# Example threshold config per priority
THRESHOLDS = {
    "low":     {"tokens": 100, "latency": 300, "complexity": 0.3},
    "medium":  {"tokens": 300, "latency": 800, "complexity": 0.6},
    "high":    {"tokens": 1000, "latency": 1500, "complexity": 1.0},
}

def check_thresholds(predictions: Dict, priority: str) -> ThresholdResult:
    limits = THRESHOLDS.get(priority, THRESHOLDS["low"])
    reasons = []

    if predictions["total_tokens"] > limits["tokens"]:
        reasons.append("Token limit exceeded")
    if predictions["latency_ms"] > limits["latency"]:
        reasons.append("Latency threshold exceeded")
    if predictions["complexity_score"] > limits["complexity"]:
        reasons.append("Complexity score too high")

    return ThresholdResult(passed=(len(reasons) == 0), failed_reasons=reasons)
