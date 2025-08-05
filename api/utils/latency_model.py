import numpy as np
from typing import Dict, Tuple, Any
from datetime import datetime

class LatencyModel:
    """Predicts API latency based on various factors"""
    
    def __init__(self):
        # Base latencies in milliseconds
        self.base_latencies = {
            "gpt-4": 800,
            "gpt-3.5-turbo": 300,
            "gpt-4-turbo": 500,
            "claude-3": 600,
            "embedding": 100
        }
        
        # Factors that affect latency
        self.token_latency_factor = 0.5  # ms per token
        self.complexity_factor = 10  # ms per complexity point
        self.time_of_day_factors = self._init_time_factors()
        
    def _init_time_factors(self) -> Dict[int, float]:
        """Initialize time-of-day multipliers (0-23 hours UTC)"""
        factors = {}
        for hour in range(24):
            if 14 <= hour <= 22:  # Peak hours (2 PM - 10 PM UTC)
                factors[hour] = 1.3
            elif 6 <= hour <= 13:  # Business hours
                factors[hour] = 1.1
            else:  # Off-peak
                factors[hour] = 0.9
        return factors
    
    def predict_latency(
        self, 
        model: str, 
        total_tokens: int, 
        complexity_score: float,
        current_time: datetime = None
    ) -> Tuple[float, Tuple[float, float]]:
        """
        Predict latency with confidence interval
        Returns: (predicted_latency_ms, (lower_bound, upper_bound))
        """
        if current_time is None:
            current_time = datetime.utcnow()
        
        # Get base latency
        base_latency = self.base_latencies.get(model, 500)
        
        # Calculate token-based latency
        token_latency = total_tokens * self.token_latency_factor
        
        # Calculate complexity-based latency
        complexity_latency = complexity_score * self.complexity_factor
        
        # Get time-of-day factor
        hour = current_time.hour
        time_factor = self.time_of_day_factors.get(hour, 1.0)
        
        # Calculate total predicted latency
        predicted_latency = (base_latency + token_latency + complexity_latency) * time_factor
        
        # Calculate confidence interval (±15%)
        margin = predicted_latency * 0.15
        confidence_interval = (
            max(0, predicted_latency - margin),
            predicted_latency + margin
        )
        
        return round(predicted_latency, 2), (round(confidence_interval[0], 2), round(confidence_interval[1], 2))
    
    def analyze_latency_factors(
        self, 
        model: str, 
        total_tokens: int, 
        complexity_score: float,
        current_time: datetime = None
    ) -> Dict[str, float]:
        """Break down latency into contributing factors"""
        if current_time is None:
            current_time = datetime.utcnow()
        
        base_latency = self.base_latencies.get(model, 500)
        token_latency = total_tokens * self.token_latency_factor
        complexity_latency = complexity_score * self.complexity_factor
        time_factor = self.time_of_day_factors.get(current_time.hour, 1.0)
        
        return {
            "base_latency_ms": round(base_latency, 2),
            "token_latency_ms": round(token_latency, 2),
            "complexity_latency_ms": round(complexity_latency, 2),
            "time_multiplier": round(time_factor, 2),
            "total_ms": round((base_latency + token_latency + complexity_latency) * time_factor, 2)
        }
    
    def suggest_optimal_time(self, current_hour: int = None) -> Dict[str, Any]:
        """Suggest optimal time for API calls"""
        if current_hour is None:
            current_hour = datetime.utcnow().hour
        
        # Find best hours (lowest factors)
        sorted_hours = sorted(self.time_of_day_factors.items(), key=lambda x: x[1])
        best_hours = sorted_hours[:3]
        
        current_factor = self.time_of_day_factors[current_hour]
        
        return {
            "current_hour_utc": current_hour,
            "current_factor": current_factor,
            "best_hours_utc": [h for h, _ in best_hours],
            "potential_improvement": f"{round((current_factor - best_hours[0][1]) / current_factor * 100, 1)}%"
        }