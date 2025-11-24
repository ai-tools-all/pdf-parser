# in heuristics/patterns.py
import re
from typing import Dict, Any, Optional
from qna_orchestrator.qna_heuristics.data_models import AnalysisContext




def classify_content_type(context: AnalysisContext) -> Optional[Dict]:
    """Classify text blocks into content types"""
    block = context.current_block
    text = block.text.strip()
    
    # Question content (question keywords)
    question_patterns = ['consider', 'which', 'with reference', 'how many', 'what is', 'who is', 'when did', 'where is', 'why did', 'how did', 'what are', 'which one', 'in which', 'select the']
    if any(pattern in text.lower() for pattern in question_patterns):
        return {"heuristic_name": "content_classification", "type": "question", "confidence": 0.8}
    
    # Option content (a), b), c), d) patterns)
    option_pattern = r'^\(?([abcd])\)?\s+'
    if re.match(option_pattern, text, re.IGNORECASE):
        return {"heuristic_name": "content_classification", "type": "option", "confidence": 0.85}
    
    # Answer marker
    if re.match(r'^Ans:\s*', text, re.IGNORECASE):
        return {"heuristic_name": "content_classification", "type": "answer", "confidence": 0.95}
    
    # Explanation (indented or following answer)
    is_indented = block.bbox[0] > context.scope_min_x + 20
    if is_indented or (context.previous_analysis and context.previous_analysis.get("type") == "answer"):
        return {"heuristic_name": "content_classification", "type": "explanation", "confidence": 0.7}
    
    return {"heuristic_name": "content_classification", "type": "continuation", "confidence": 0.5}

def detect_answer_boundaries(context: AnalysisContext) -> Optional[Dict]:
    """Detect answer markers and separate from explanations"""
    block = context.current_block
    
    # Pattern: "Ans: (a)" or "Ans: a"
    ans_pattern = r'^Ans:\s*\(?([abcd]|[1-4])\)?'
    match = re.match(ans_pattern, block.text.strip(), re.IGNORECASE)
    
    if match:
        answer_value = match.group(1).lower()
        explanation_start = match.end()
        explanation_text = block.text[explanation_start:].strip()
        
        return {
            "heuristic_name": "answer_boundary",
            "type": "answer_marker",
            "answer": answer_value,
            "has_explanation": len(explanation_text) > 0,
            "explanation_text": explanation_text,
            "confidence": 0.98
        }
    
    return None

def detect_question_start_enhanced(context: AnalysisContext) -> Optional[Dict]:
    """Enhanced question start detection for VisionIAS format."""
    block = context.current_block
    
    # VisionIAS Format: "1. The transition zone..."
    # We strictly look for the number pattern here.
    # The 'clustering' check happens in the Assembler.
    
    question_num_pattern = r'^\s*(\d{1,3})\.'  # Matches 1. to 999.
    match = re.match(question_num_pattern, block.text.strip())
    
    if match:
        return {
            "heuristic_name": "question_start",
            "confidence": 0.95,
            "question_number": match.group(1),
            "is_question_start": True
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