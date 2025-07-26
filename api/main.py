from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Dict

app = FastAPI()

class QueryContext(BaseModel):
    user_id: str
    role: Optional[str] = None
    client_id: Optional[str] = None
    location: Optional[str] = None
    device: Optional[Literal["desktop", "mobile", "tablet"]] = None
    behavior_summary: Optional[str] = None
    urgency: Optional[str] = None  # e.g. "low", "medium", "high"

class PredictRequest(BaseModel):
    query: str
    context: QueryContext

class Suggestion(BaseModel):
    type: Literal["performance", "cost", "accuracy"]
    message: str

class PredictResponse(BaseModel):
    status: Literal["ok", "suggest_improvement", "rejected"]
    predicted_latency: str
    estimated_cost: str
    suggestions: List[Suggestion]
    alternatives: Optional[List[str]] = []

@app.post("/api/predict", response_model=PredictResponse)
def predict_query(data: PredictRequest):
    # Placeholder logic
    suggestions = [
        {"type": "performance", "message": "Add date filter to reduce scan"},
        {"type": "cost", "message": "Avoid wildcard match"},
        {"type": "performance", "message": "Use indexed fields"},
    ]
    return {
        "status": "suggest_improvement",
        "predicted_latency": "12s",
        "estimated_cost": "$0.45",
        "suggestions": suggestions[:3],
        "alternatives": ["Schedule report for off-peak"],
    }
