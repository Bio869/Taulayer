import json
from typing import Dict, Any, List
from enum import Enum

class ComplexityFactor(Enum):
    NESTED_DEPTH = "deep_nesting"
    LARGE_ARRAYS = "large_arrays"
    COMPLEX_PROMPTS = "complex_prompts"
    MULTIPLE_TOOLS = "multiple_tools"
    LONG_CONTEXT = "long_context"
    SPECIALIZED_TASK = "specialized_task"
    MULTI_STEP = "multi_step_reasoning"

class RequestAnalyzer:
    """Analyzes API request complexity"""
    
    def __init__(self):
        self.complexity_weights = {
            ComplexityFactor.NESTED_DEPTH: 15,
            ComplexityFactor.LARGE_ARRAYS: 10,
            ComplexityFactor.COMPLEX_PROMPTS: 20,
            ComplexityFactor.MULTIPLE_TOOLS: 25,
            ComplexityFactor.LONG_CONTEXT: 15,
            ComplexityFactor.SPECIALIZED_TASK: 20,
            ComplexityFactor.MULTI_STEP: 30
        }
        
        self.specialized_keywords = [
            "analyze", "summarize", "translate", "generate code",
            "debug", "optimize", "explain", "compare", "evaluate"
        ]
    
    def analyze_complexity(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze request complexity and return score with factors"""
        factors = []
        score = 0
        
        # Check nesting depth
        depth = self._get_max_depth(payload)
        if depth > 3:
            factors.append(ComplexityFactor.NESTED_DEPTH)
            score += self.complexity_weights[ComplexityFactor.NESTED_DEPTH]
        
        # Check for large arrays
        if self._has_large_arrays(payload):
            factors.append(ComplexityFactor.LARGE_ARRAYS)
            score += self.complexity_weights[ComplexityFactor.LARGE_ARRAYS]
        
        # Analyze prompt complexity
        prompt_complexity = self._analyze_prompt_complexity(payload)
        if prompt_complexity["is_complex"]:
            factors.append(ComplexityFactor.COMPLEX_PROMPTS)
            score += self.complexity_weights[ComplexityFactor.COMPLEX_PROMPTS]
        
        # Check for multiple tools/functions
        if self._uses_multiple_tools(payload):
            factors.append(ComplexityFactor.MULTIPLE_TOOLS)
            score += self.complexity_weights[ComplexityFactor.MULTIPLE_TOOLS]
        
        # Check context length
        if self._has_long_context(payload):
            factors.append(ComplexityFactor.LONG_CONTEXT)
            score += self.complexity_weights[ComplexityFactor.LONG_CONTEXT]
        
        # Check for specialized tasks
        if self._is_specialized_task(payload):
            factors.append(ComplexityFactor.SPECIALIZED_TASK)
            score += self.complexity_weights[ComplexityFactor.SPECIALIZED_TASK]
        
        # Determine complexity level
        if score < 20:
            level = "low"
        elif score < 40:
            level = "medium"
        elif score < 60:
            level = "high"
        else:
            level = "very_high"
        
        return {
            "score": min(score, 100),
            "level": level,
            "factors": [f.value for f in factors],
            "details": {
                "max_depth": depth,
                "prompt_complexity": prompt_complexity,
                "factor_count": len(factors)
            }
        }
    
    def _get_max_depth(self, obj: Any, current_depth: int = 0) -> int:
        """Get maximum nesting depth of object"""
        if isinstance(obj, dict):
            if not obj:
                return current_depth
            return max(self._get_max_depth(v, current_depth + 1) for v in obj.values())
        elif isinstance(obj, list):
            if not obj:
                return current_depth
            return max(self._get_max_depth(item, current_depth + 1) for item in obj)
        else:
            return current_depth
    
    def _has_large_arrays(self, obj: Any, threshold: int = 50) -> bool:
        """Check if object contains large arrays"""
        if isinstance(obj, list) and len(obj) > threshold:
            return True
        elif isinstance(obj, dict):
            return any(self._has_large_arrays(v) for v in obj.values())
        return False
    
    def _analyze_prompt_complexity(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze prompt/message complexity"""
        prompt_text = ""
        
        # Extract prompt text from various formats
        if "prompt" in payload:
            prompt_text = str(payload["prompt"])
        elif "messages" in payload:
            messages = payload["messages"]
            if isinstance(messages, list):
                prompt_text = " ".join(msg.get("content", "") for msg in messages if isinstance(msg, dict))
        
        word_count = len(prompt_text.split())
        has_code = "```" in prompt_text or "def " in prompt_text or "function" in prompt_text
        has_multiple_questions = prompt_text.count("?") > 2
        
        is_complex = word_count > 200 or has_code or has_multiple_questions
        
        return {
            "is_complex": is_complex,
            "word_count": word_count,
            "has_code": has_code,
            "question_count": prompt_text.count("?")
        }
    
    def _uses_multiple_tools(self, payload: Dict[str, Any]) -> bool:
        """Check if request uses multiple tools/functions"""
        if "tools" in payload and isinstance(payload["tools"], list):
            return len(payload["tools"]) > 1
        if "functions" in payload and isinstance(payload["functions"], list):
            return len(payload["functions"]) > 1
        return False
    
    def _has_long_context(self, payload: Dict[str, Any]) -> bool:
        """Check if request has long context"""
        json_str = json.dumps(payload)
        return len(json_str) > 5000  # Characters, not tokens
    
    def _is_specialized_task(self, payload: Dict[str, Any]) -> bool:
        """Check if request is for specialized task"""
        payload_str = json.dumps(payload).lower()
        return any(keyword in payload_str for keyword in self.specialized_keywords)
    
    def suggest_optimizations(self, complexity_analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Suggest optimizations based on complexity factors"""
        suggestions = []
        factors = complexity_analysis.get("factors", [])
        
        if ComplexityFactor.NESTED_DEPTH.value in factors:
            suggestions.append({
                "issue": "Deep nesting detected",
                "suggestion": "Flatten nested structures where possible",
                "impact": "10-15% performance improvement"
            })
        
        if ComplexityFactor.LARGE_ARRAYS.value in factors:
            suggestions.append({
                "issue": "Large arrays in payload",
                "suggestion": "Consider pagination or chunking large datasets",
                "impact": "20-30% latency reduction"
            })
        
        if ComplexityFactor.LONG_CONTEXT.value in factors:
            suggestions.append({
                "issue": "Long context detected",
                "suggestion": "Summarize or compress context when possible",
                "impact": "15-25% token reduction"
            })
        
        if ComplexityFactor.MULTIPLE_TOOLS.value in factors:
            suggestions.append({
                "issue": "Multiple tools/functions used",
                "suggestion": "Consider combining related functions",
                "impact": "10-20% processing time reduction"
            })
        
        return suggestions