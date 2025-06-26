# in heuristics/patterns.py
import re
from typing import Dict, Any, Optional
from data_models import AnalysisContext

def analyze_question_number(context: AnalysisContext) -> Optional[Dict[str, Any]]:
    """Checks if a block starts with a question number pattern."""
    regex = context.config['HEURISTICS']['PATTERNS']['REGEX_QUESTION']
    match = re.match(regex, context.current_block.text)
    if match:
        return {
            "heuristic_name": "pattern_match",
            "type": "question_start",
            "value": int(match.group(1))
        }
    return None

def analyze_option_letter(context: AnalysisContext) -> Optional[Dict[str, Any]]:
    """Checks if a block starts with an option letter like (a)."""
    regex = context.config['HEURISTICS']['PATTERNS']['REGEX_OPTION']
    match = re.match(regex, context.current_block.text)
    if match:
        return {
            "heuristic_name": "pattern_match",
            "type": "option",
            "value": match.group(1).lower()
        }
    return None

def analyze_answer_marker(context: AnalysisContext) -> Optional[Dict[str, Any]]:
    """Checks if a block starts with an answer marker like Ans: (c)."""
    regex = context.config['HEURISTICS']['PATTERNS']['REGEX_ANSWER']
    match = re.match(regex, context.current_block.text, re.IGNORECASE)
    if match:
        return {
            "heuristic_name": "pattern_match",
            "type": "answer_marker",
            "value": match.group(1).lower()
        }
    return None