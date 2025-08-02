# taulayer_api/routers/predict.py

from fastapi import APIRouter, HTTPException
from taulayer_api.models import PredictInput, PredictOutput
from taulayer_api.logic.predictor import analyze_request
from taulayer_api.services.logger import log_request

router = APIRouter(prefix="/api", tags=["predict"])

@router.post("/predict", response_model=PredictOutput)
async def predict(payload: PredictInput):
    try:
        result = analyze_request(payload)
        await log_request(payload, result)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))