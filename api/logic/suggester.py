from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class Suggester:
    """Generates rule-based optimization suggestions based on predictions"""
    
    def __init__(self):
        self.suggestion_templates = {
            "high_tokens": {
                "title": "Reduce Token Usage",
                "description": "Your request uses {tokens} tokens. Consider reducing prompt length or using more concise instructions.",
                "impact": "Up to 30% cost reduction",
                "priority": 4,
                "implementation_effort": "low"
            },
            "high_complexity": {
                "title": "Simplify Request Structure",
                "description": "Complex nested structures detected. Flatten JSON objects and reduce nesting depth.",
                "impact": "15-20% latency reduction",
                "priority": 3,
                "implementation_effort": "medium"
            },
            "peak_hours": {
                "title": "Schedule for Off-Peak Hours",
                "description": "Current time has {multiplier}x latency. Best hours are {best_hours} UTC.",
                "impact": "{improvement} latency reduction",
                "priority": 2,
                "implementation_effort": "low"
            },
            "large_context": {
                "title": "Implement Context Compression",
                "description": "Large context detected ({size} chars). Use summarization or context windowing.",
                "impact": "20-40% token reduction",
                "priority": 5,
                "implementation_effort": "high"
            },
            "multiple_operations": {
                "title": "Batch Similar Operations",
                "description": "Multiple similar operations detected. Consider batching requests.",
                "impact": "50% reduction in API calls",
                "priority": 4,
                "implementation_effort": "medium"
            },
            "expensive_model": {
                "title": "Consider Model Downgrade",
                "description": "Task complexity suggests {suggested_model} would suffice instead of {current_model}.",
                "impact": "60-80% cost reduction",
                "priority": 5,
                "implementation_effort": "low"
            }
        }
    
    async def generate_suggestions(self, predictions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate optimization suggestions based on predictions"""
        suggestions = []
        
        try:
            # Check token usage
            if predictions.get("total_tokens", 0) > 1000:
                suggestion = self.suggestion_templates["high_tokens"].copy()
                suggestion["description"] = suggestion["description"].format(
                    tokens=predictions["total_tokens"]
                )
                suggestions.append(suggestion)
            
            # Check complexity
            complexity_level = predictions.get("complexity_level", "low")
            if complexity_level in ["high", "very_high"]:
                suggestions.append(self.suggestion_templates["high_complexity"])
            
            # Check timing
            reasoning = predictions.get("reasoning", {})
            optimal_timing = reasoning.get("optimal_timing", {})
            if optimal_timing.get("current_factor", 1.0) > 1.2:
                suggestion = self.suggestion_templates["peak_hours"].copy()
                suggestion["description"] = suggestion["description"].format(
                    multiplier=optimal_timing["current_factor"],
                    best_hours=", ".join(map(str, optimal_timing.get("best_hours_utc", [])))
                )
                suggestion["impact"] = suggestion["impact"].format(
                    improvement=optimal_timing.get("potential_improvement", "10-20%")
                )
                suggestions.append(suggestion)
            
            # Check for large context
            token_dist = reasoning.get("token_distribution", {})
            if any(count > 500 for count in token_dist.get("token_counts", {}).values()):
                largest_component = max(token_dist.get("token_counts", {}).items(), 
                                      key=lambda x: x[1], default=("unknown", 0))
                suggestion = self.suggestion_templates["large_context"].copy()
                suggestion["description"] = suggestion["description"].format(
                    size=largest_component[1] * 4  # Approximate chars
                )
                suggestions.append(suggestion)
            
            # Check model selection
            if predictions.get("complexity_score", 0) < 30:
                current_model = reasoning.get("latency_factors", {}).get("model", "gpt-4")
                if current_model in ["gpt-4", "claude-3"]:
                    suggestion = self.suggestion_templates["expensive_model"].copy()
                    suggestion["description"] = suggestion["description"].format(
                        current_model=current_model,
                        suggested_model="gpt-3.5-turbo"
                    )
                    suggestions.append(suggestion)
            
            # Add code examples where applicable
            for suggestion in suggestions:
                suggestion["code_example"] = self._get_code_example(suggestion["title"])
            
            # Sort by priority
            suggestions.sort(key=lambda x: x["priority"], reverse=True)
            
            logger.info(f"Generated {len(suggestions)} optimization suggestions")
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Suggestion generation error: {str(e)}")
            return []
    
    def _get_code_example(self, suggestion_title: str) -> str:
        """Get code example for a suggestion"""
        examples = {
            "Reduce Token Usage": """# Before
prompt = "Please analyze this very long text and provide a comprehensive detailed analysis..."

# After
prompt = "Summarize key points from this text:"
# Use structured output format to reduce tokens""",
            
            "Simplify Request Structure": """# Before
data = {
    "user": {
        "profile": {
            "settings": {
                "preferences": {...}
            }
        }
    }
}

# After
data = {
    "user_id": "123",
    "preferences": {...}
}""",
            
            "Schedule for Off-Peak Hours": """import asyncio
from datetime import datetime, time

async def run_at_optimal_time(task):
    optimal_hours = [2, 3, 4]  # UTC
    current_hour = datetime.utcnow().hour
    
    if current_hour not in optimal_hours:
        wait_hours = min((h - current_hour) % 24 for h in optimal_hours)
        await asyncio.sleep(wait_hours * 3600)
    
    return await task()""",
            
            "Consider Model Downgrade": """# For simple tasks, use gpt-3.5-turbo
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",  # Instead of gpt-4
    messages=[{"role": "user", "content": prompt}],
    temperature=0.7
)"""
        }
        
        return examples.get(suggestion_title, "")