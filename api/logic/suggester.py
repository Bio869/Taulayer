# api/logic/suggester.py

from typing import List

def generate_suggestions(prompt: str) -> List[str]:
    """
    Return stub suggestions to help user refine the prompt.
    Real implementation might use prompt classification or LLM tips.
    """
    return [
        "Try reducing the scope of your request",
        "Add filters like dates or categories",
        "Avoid overly broad or open-ended phrasing",
        "Run this during off-peak hours to reduce latency"
    ]
