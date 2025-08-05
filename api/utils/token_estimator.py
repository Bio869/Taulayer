import json
import tiktoken
from typing import Dict, Any, Union

class TokenEstimator:
    """Estimates token usage for API requests"""
    
    def __init__(self, model: str = "gpt-4"):
        self.model = model
        try:
            self.encoder = tiktoken.encoding_for_model(model)
        except:
            # Fallback to cl100k_base encoding
            self.encoder = tiktoken.get_encoding("cl100k_base")
        
        # Cost per 1K tokens (example rates)
        self.cost_per_1k_input = 0.03  # $0.03 per 1K input tokens
        self.cost_per_1k_output = 0.06  # $0.06 per 1K output tokens
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string"""
        return len(self.encoder.encode(text))
    
    def estimate_json_tokens(self, data: Union[Dict, list, Any]) -> int:
        """Estimate tokens for JSON data"""
        json_str = json.dumps(data, separators=(',', ':'))
        return self.count_tokens(json_str)
    
    def estimate_request_tokens(self, payload: Dict[str, Any]) -> Dict[str, int]:
        """Estimate tokens for an API request"""
        # Base overhead for API formatting
        base_overhead = 10
        
        # Count tokens in the payload
        payload_tokens = self.estimate_json_tokens(payload)
        
        # Estimate output tokens based on input complexity
        # This is a heuristic - adjust based on your use case
        if "messages" in payload:
            # Chat completion request
            output_estimate = min(payload_tokens * 2, 2000)
        elif "prompt" in payload:
            # Completion request
            max_tokens = payload.get("max_tokens", 1000)
            output_estimate = min(payload_tokens * 1.5, max_tokens)
        else:
            # Generic estimation
            output_estimate = payload_tokens
        
        return {
            "input_tokens": payload_tokens + base_overhead,
            "output_tokens": int(output_estimate),
            "total_tokens": payload_tokens + base_overhead + int(output_estimate)
        }
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate estimated cost based on token usage"""
        input_cost = (input_tokens / 1000) * self.cost_per_1k_input
        output_cost = (output_tokens / 1000) * self.cost_per_1k_output
        return round(input_cost + output_cost, 4)
    
    def analyze_token_distribution(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze token distribution across different parts of the payload"""
        distribution = {}
        
        for key, value in payload.items():
            if isinstance(value, str):
                distribution[key] = self.count_tokens(value)
            elif isinstance(value, (dict, list)):
                distribution[key] = self.estimate_json_tokens(value)
            else:
                distribution[key] = self.count_tokens(str(value))
        
        total = sum(distribution.values())
        percentages = {k: round((v/total) * 100, 2) for k, v in distribution.items()}
        
        return {
            "token_counts": distribution,
            "percentages": percentages,
            "total": total
        }