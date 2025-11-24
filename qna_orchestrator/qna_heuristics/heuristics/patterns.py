# in heuristics/patterns.py
import re
from typing import Dict, Any, Optional
from qna_orchestrator.qna_heuristics.data_models import AnalysisContext




def classify_content_type(context: AnalysisContext) -> Optional[Dict]:
    """Classify text blocks into content types"""
    block = context.current_block
    text = block.text.strip()
    
    # Question content (bold + question patterns)
    if 'bold' in block.font_name.lower() and any(pattern in text.lower() 
                                                for pattern in ['consider', 'which', 'with reference']):
        return {"heuristic_name": "content_classification", "type": "question", "confidence": 0.9}
    
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
    """Enhanced question start detection using multiple signals"""
    block = context.current_block
    
    # Signal 1: Bold formatting
    is_bold = 'bold' in block.font_name.lower() or getattr(block, 'font_weight', 400) > 600
    
    # Signal 2: Question number pattern
    question_num_pattern = r'^\d+\.\s*'
    has_question_number = re.match(question_num_pattern, block.text.strip())
    
    # Signal 3: Question keywords
    question_keywords = ['consider the following', 'which of the following', 'with reference to']
    has_question_keyword = any(keyword in block.text.lower() for keyword in question_keywords)
    
    # Combined detection
    if is_bold and has_question_number and has_question_keyword:
        return {
            "heuristic_name": "enhanced_question_start",
            "confidence": 0.95,
            "question_number": has_question_number.group().strip('.\t '),
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