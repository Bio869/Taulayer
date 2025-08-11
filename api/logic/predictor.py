# api/logic/predictor.py

from typing import Dict, List
from pydantic import BaseModel
import random

# NEW: import your utils
from utils.token_estimator import estimate_tokens
from utils.latency_model import estimate_latency
from utils.complexity_estimator import estimate_complexity

class ThresholdResult(BaseModel):
    passed: bool
    failed_reasons: List[str] = []

# (keep your thresholds as-is for now)
THRESHOLDS = {
    "low":     {"tokens": 300,  "latency": 300,  "complexity": 0.3},
    "medium":  {"tokens": 500,  "latency": 800,  "complexity": 0.6},
    "high":    {"tokens": 1000, "latency": 1500, "complexity": 1.0},
}

def analyze_request(prompt: str) -> Dict:
    return {
        "total_tokens":     estimate_tokens(prompt),
        "latency_ms":       estimate_latency(prompt),
        "complexity_score": estimate_complexity(prompt),
        "vector_embedding": generate_fake_embedding(),
    }

def generate_fake_embedding(dim: int = 1536) -> list:
    return [random.uniform(-1, 1) for _ in range(dim)]

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
