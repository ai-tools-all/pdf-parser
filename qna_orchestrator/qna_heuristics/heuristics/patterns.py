# in heuristics/patterns.py
import re
from typing import Dict, Any, Optional
from qna_orchestrator.qna_heuristics.data_models import AnalysisContext

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

def analyze_descriptive_question_start(context: AnalysisContext) -> Optional[Dict[str, Any]]:
    """
    Detects question starts that begin with descriptive text rather than numbers.
    Common patterns: 'Consider the following', 'Which of the following', etc.
    """
    text = context.current_block.text.strip()
    
    # Patterns that commonly start MCQ questions
    descriptive_patterns = [
        r'^Consider\s+the\s+following',
        r'^Which\s+of\s+the\s+following',
        r'^What\s+is\s+the',
        r'^How\s+many\s+of\s+the',
        r'^Identify\s+the',
        r'^Select\s+the',
        r'^Choose\s+the',
        r'^Mark\s+the',
        r'^Find\s+the',
        r'^Determine\s+the'
    ]
    
    for pattern in descriptive_patterns:
        if re.match(pattern, text, re.IGNORECASE):
            return {
                "heuristic_name": "pattern_match", 
                "type": "descriptive_question_start",
                "pattern": pattern,
                "confidence": "high"
            }
    
    return None

def analyze_explanation_start(context: AnalysisContext) -> Optional[Dict[str, Any]]:
    """
    Detects the start of answer explanations.
    Common patterns: 'Statement 1 is correct:', 'Explanation:', etc.
    """
    text = context.current_block.text.strip()
    
    explanation_patterns = [
        r'^Statement\s+\d+\s+is\s+(correct|incorrect)',
        r'^Explanation\s*:',
        r'^Solution\s*:',
        r'^Answer\s*:',
        r'^Reason\s*:',
        r'^Justification\s*:'
    ]
    
    for pattern in explanation_patterns:
        if re.match(pattern, text, re.IGNORECASE):
            return {
                "heuristic_name": "pattern_match",
                "type": "explanation_start", 
                "pattern": pattern,
                "confidence": "high"
            }
    
    return None