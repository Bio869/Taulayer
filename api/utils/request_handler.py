import re
import numpy as np
from typing import Dict, Any, List, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ComplexityFactor(Enum):
    VAGUE_TERMS = "vague_terms"
    OPEN_ENDED = "open_ended"
    LACK_OF_CONSTRAINTS = "lack_of_constraints"
    EXPLORATORY_INTENT = "exploratory_intent"
    VAST_SCOPE = "vast_scope"
    LOW_SPECIFICITY = "low_specificity"
    MULTIPLE_TOPICS = "multiple_topics"
    NO_TIME_SCOPE = "no_time_scope"

class RequestAnalyzer:
    """Advanced request analyzer with NLP-based complexity scoring"""
    
    def __init__(self):
        # Vague terms and patterns
        self.vague_terms = [
            "all", "everything", "anything", "something", "stuff",
            "things", "various", "multiple", "several", "many",
            "some", "any", "whatever", "etc", "and so on"
        ]
        
        # Exploratory intent patterns
        self.exploratory_patterns = [
            r"tell me about", r"what's your opinion on", r"explore",
            r"describe", r"discuss", r"what are your thoughts on",
            r"explain", r"elaborate", r"walk me through", r"overview"
        ]
        
        # Constraint patterns
        self.constraint_patterns = [
            r'\b(only|just|exactly|specifically)\b',
            r'\b(filter by|limit to|where)\b',
            r'\b(greater than|less than|equal to|between)\b',
            r'\b(show only|display only)\b',
            r'\b(top \d+|first \d+|last \d+)\b',
            r'\b(from|to|until|before|after)\b'
        ]
        
        # Specific entity patterns
        self.specific_entity_patterns = [
            r'\b(Apple|Google|Microsoft|Amazon|Tesla)\b',  # Specific companies
            r'\b(Q[1-4]\s+\d{4})\b',  # Quarter and year
            r'\b(\d{4}-\d{2}-\d{2})\b',  # Date format
            r'\b(\$\d+(?:\.\d+)?[KMB]?)\b',  # Money amounts
            r'\b(\d+(?:\.\d+)?%)\b',  # Percentages
        ]
        
        # Domain-specific vast scope indicators
        self.vast_scope_indicators = {
            "all stocks": 10000,
            "all companies": 50000,
            "s&p 500": 500,
            "fortune 500": 500,
            "nasdaq": 3000,
            "entire market": 100000,
            "global economy": 1000000,
            "all sectors": 1000,
            "all industries": 5000
        }
    
    def analyze_complexity(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze request complexity with advanced NLP techniques
        """
        prompt = payload.get("prompt", "")
        conversation_history = payload.get("conversation_history", [])
        
        # Initialize scores
        scores = {
            "vagueness_score": 0.0,
            "constraint_score": 0.0,
            "specificity_score": 0.0,
            "scope_score": 0.0,
            "intent_score": 0.0,
            "temporal_score": 0.0,
            "context_cohesion_score": 0.0
        }
        
        factors = []
        
        # 1. Analyze vagueness
        vague_count = sum(1 for term in self.vague_terms if term in prompt.lower())
        word_count = len(prompt.split())
        if word_count > 0:
            scores["vagueness_score"] = min(vague_count / word_count * 10, 1.0)
            if scores["vagueness_score"] > 0.3:
                factors.append(ComplexityFactor.VAGUE_TERMS)
        
        # 2. Analyze constraints
        constraint_count = sum(1 for pattern in self.constraint_patterns 
                             if re.search(pattern, prompt, re.IGNORECASE))
        scores["constraint_score"] = 1.0 - min(constraint_count / 3, 1.0)  # Inverted: fewer constraints = higher score
        if constraint_count < 2:
            factors.append(ComplexityFactor.LACK_OF_CONSTRAINTS)
        
        # 3. Analyze specificity
        specific_entity_count = sum(1 for pattern in self.specific_entity_patterns 
                                  if re.search(pattern, prompt, re.IGNORECASE))
        scores["specificity_score"] = 1.0 - min(specific_entity_count / 3, 1.0)  # Inverted: fewer specific entities = higher score
        if specific_entity_count < 1:
            factors.append(ComplexityFactor.LOW_SPECIFICITY)
        
        # 4. Analyze scope
        implied_entities = self._calculate_implied_entities(prompt)
        if implied_entities > 100:
            scores["scope_score"] = min(np.log10(implied_entities) / 5, 1.0)
            factors.append(ComplexityFactor.VAST_SCOPE)
        
        # 5. Analyze intent
        is_exploratory = any(re.search(pattern, prompt, re.IGNORECASE) 
                           for pattern in self.exploratory_patterns)
        scores["intent_score"] = 1.0 if is_exploratory else 0.0
        if is_exploratory:
            factors.append(ComplexityFactor.EXPLORATORY_INTENT)
        
        # 6. Analyze temporal scope
        has_time_constraint = bool(re.search(r'\b(today|yesterday|tomorrow|this week|last month|Q[1-4]|20\d{2})\b', 
                                           prompt, re.IGNORECASE))
        scores["temporal_score"] = 0.0 if has_time_constraint else 0.5
        if not has_time_constraint:
            factors.append(ComplexityFactor.NO_TIME_SCOPE)
        
        # 7. Analyze context cohesion
        if conversation_history:
            scores["context_cohesion_score"] = self._calculate_context_cohesion(prompt, conversation_history)
        
        # Calculate overall complexity score (0-100)
        weights = {
            "vagueness_score": 0.20,
            "constraint_score": 0.15,
            "specificity_score": 0.15,
            "scope_score": 0.20,
            "intent_score": 0.15,
            "temporal_score": 0.10,
            "context_cohesion_score": 0.05
        }
        
        overall_score = sum(scores[key] * weights[key] for key in weights) * 100
        
        # Determine complexity level
        if overall_score < 20:
            level = "low"
        elif overall_score < 40:
            level = "medium"
        elif overall_score < 60:
            level = "high"
        else:
            level = "very_high"
        
        # Calculate open-endedness score (similar to your NLP approach)
        overall_vague_open_ended_score = (
            scores["vagueness_score"] * 0.3 +
            scores["constraint_score"] * 0.2 +
            scores["intent_score"] * 0.2 +
            scores["scope_score"] * 0.15 +
            (1 - scores["context_cohesion_score"]) * 0.15
        )
        
        if has_time_constraint:
            overall_vague_open_ended_score *= 0.5
        
        return {
            "score": overall_score,
            "level": level,
            "factors": [f.value for f in factors],
            "overall_vague_open_ended_score": min(max(overall_vague_open_ended_score, 0), 1),
            "details": {
                "scores": scores,
                "implied_entities": implied_entities,
                "has_time_constraint": has_time_constraint,
                "is_exploratory": is_exploratory,
                "constraint_count": constraint_count,
                "specific_entity_count": specific_entity_count,
                "vague_term_count": vague_count
            }
        }
    
    def _calculate_implied_entities(self, prompt: str) -> int:
        """Calculate the number of entities implied by the request"""
        prompt_lower = prompt.lower()
        
        for indicator, count in self.vast_scope_indicators.items():
            if indicator in prompt_lower:
                return count
        
        # Check for numeric indicators
        match = re.search(r'(?:all|every|each)\s+(\d+)', prompt_lower)
        if match:
            return int(match.group(1))
        
        # Default to 1 if no vast scope detected
        return 1
    
    def _calculate_context_cohesion(self, prompt: str, history: List[str]) -> float:
        """
        Calculate context cohesion between current prompt and conversation history
        Simple implementation using keyword overlap
        """
        if not history:
            return 1.0
        
        # Get keywords from current prompt
        current_keywords = set(re.findall(r'\b\w{4,}\b', prompt.lower()))
        
        # Get keywords from last 3 turns of history
        history_keywords = set()
        for turn in history[-3:]:
            history_keywords.update(re.findall(r'\b\w{4,}\b', turn.lower()))
        
        # Calculate overlap
        if not history_keywords:
            return 0.5
        
        overlap = len(current_keywords & history_keywords)
        total = len(current_keywords | history_keywords)
        
        return overlap / total if total > 0 else 0.0
    
    def suggest_refinements(self, complexity_analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate refinement suggestions based on complexity analysis"""
        suggestions = []
        details = complexity_analysis.get("details", {})
        
        if ComplexityFactor.VAGUE_TERMS.value in complexity_analysis.get("factors", []):
            suggestions.append({
                "issue": "Vague terminology detected",
                "suggestion": "Replace general terms with specific entities, metrics, or criteria",
                "example": "Instead of 'show me all good stocks', try 'show me stocks with P/E ratio < 20 and market cap > $10B'",
                "impact": "50-70% reduction in response scope"
            })
        
        if ComplexityFactor.LACK_OF_CONSTRAINTS.value in complexity_analysis.get("factors", []):
            suggestions.append({
                "issue": "No filtering constraints specified",
                "suggestion": "Add specific filters like time range, thresholds, or categories",
                "example": "Add constraints like 'in the last quarter', 'top 10 by revenue', or 'technology sector only'",
                "impact": "60-80% reduction in processing time"
            })
        
        if ComplexityFactor.VAST_SCOPE.value in complexity_analysis.get("factors", []):
            entity_count = details.get("implied_entities", 0)
            suggestions.append({
                "issue": f"Request implies processing {entity_count:,} entities",
                "suggestion": "Narrow the scope with specific criteria or sampling",
                "example": "Focus on 'top 50 by market cap' or 'random sample of 100'",
                "impact": "90% reduction in data volume"
            })
        
        if ComplexityFactor.NO_TIME_SCOPE.value in complexity_analysis.get("factors", []):
            suggestions.append({
                "issue": "No time boundaries specified",
                "suggestion": "Add temporal constraints to limit data range",
                "example": "Specify 'last 30 days', 'Q3 2024', or 'year-to-date'",
                "impact": "40-60% reduction in data processing"
            })
        
        if ComplexityFactor.EXPLORATORY_INTENT.value in complexity_analysis.get("factors", []):
            suggestions.append({
                "issue": "Open-ended exploratory request",
                "suggestion": "Define specific questions or metrics of interest",
                "example": "Instead of 'tell me about', ask 'what is the 3-month trend for...' or 'compare X and Y by...'",
                "impact": "More focused and actionable insights"
            })
        
        return suggestions