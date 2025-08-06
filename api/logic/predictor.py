from typing import Dict, Any, Optional
import json
import logging
from datetime import datetime

# Import your utilities
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.token_estimator import TokenEstimator
from utils.latency_model import LatencyModel
from utils.request_handler import RequestAnalyzer

logger = logging.getLogger(__name__)

class Predictor:
    """Orchestrates prediction of latency, tokens, and complexity"""
    
    def __init__(self):
        self.token_estimator = TokenEstimator()
        self.latency_model = LatencyModel()
        self.request_handler = RequestAnalyzer()
    
    async def analyze_request(self, prompt: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze an API request and return predictions
        """
        try:
            # Prepare the payload for analysis
            payload = {
                "prompt": prompt,
                "model": metadata.get("model", "gpt-4") if metadata else "gpt-4"
            }
            
            # Add any additional metadata
            if metadata:
                payload.update(metadata)
            
            # 1. Estimate tokens
            token_result = self.token_estimator.estimate_request_tokens(payload)
            token_distribution = self.token_estimator.analyze_token_distribution(payload)
            
            # 2. Analyze complexity
            complexity_result = self.request_handler.analyze_complexity(payload)
            
            # 3. Predict latency
            predicted_latency, confidence_interval = self.latency_model.predict_latency(
                model=payload.get("model", "gpt-4"),
                total_tokens=token_result["total_tokens"],
                complexity_score=complexity_result["score"]
            )
            
            # 4. Get latency breakdown
            latency_factors = self.latency_model.analyze_latency_factors(
                model=payload.get("model", "gpt-4"),
                total_tokens=token_result["total_tokens"],
                complexity_score=complexity_result["score"]
            )
            
            # 5. Calculate cost
            estimated_cost = self.token_estimator.calculate_cost(
                input_tokens=token_result["input_tokens"],
                output_tokens=token_result["output_tokens"]
            )
            
            # 6. Get optimal timing suggestion
            optimal_time = self.latency_model.suggest_optimal_time()
            
            # 7. Create embedding (simplified - in production, use actual embedding model)
            embedding = self._create_simple_embedding(prompt)
            
            # Compile results
            predictions = {
                "latency_ms": int(predicted_latency),
                "latency_confidence_interval": {
                    "lower": confidence_interval[0],
                    "upper": confidence_interval[1]
                },
                "input_tokens": token_result["input_tokens"],
                "output_tokens": token_result["output_tokens"],
                "total_tokens": token_result["total_tokens"],
                "estimated_cost": estimated_cost,
                "complexity_score": complexity_result["score"],
                "complexity_level": complexity_result["level"],
                "complexity_factors": complexity_result["factors"],
                "embedding": embedding,
                "reasoning": {
                    "token_distribution": token_distribution,
                    "latency_factors": latency_factors,
                    "complexity_details": complexity_result["details"],
                    "optimal_timing": optimal_time
                },
                "analyzed_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Prediction completed: {predicted_latency}ms, {token_result['total_tokens']} tokens, complexity {complexity_result['score']}")
            
            return predictions
            
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            raise
    
    def _create_simple_embedding(self, text: str) -> list:
        """Create a simple embedding (placeholder for real embedding model)"""
        # In production, use OpenAI embeddings or similar
        # This is just a simple hash-based placeholder
        import hashlib
        hash_object = hashlib.md5(text.encode())
        hash_hex = hash_object.hexdigest()
        # Convert to list of floats between -1 and 1
        embedding = []
        for i in range(0, 32, 2):
            value = int(hash_hex[i:i+2], 16) / 127.5 - 1
            embedding.append(round(value, 4))
        return embedding