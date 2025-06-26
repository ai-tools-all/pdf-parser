# in heuristics/layout.py
from typing import Dict, Any, Optional
from qna_orchestrator.qna_heuristics.data_models import AnalysisContext

def analyze_indentation(context: AnalysisContext) -> Optional[Dict[str, Any]]:
    """Checks if a block is indented relative to the column's minimum x-coordinate."""
    cfg = context.config['HEURISTICS']['LAYOUT']
    indent_threshold = cfg['INDENTATION_THRESHOLD']

    # Use pre-calculated minimum x for the scope
    indentation = context.current_block.bbox[0] - context.scope_min_x

    if indentation > indent_threshold:
        return {
            "heuristic_name": "indentation",
            "is_indented": True,
            "indent_amount": round(indentation, 2)
        }
    return None

def analyze_font_style(context: AnalysisContext) -> Optional[Dict[str, Any]]:
    """
    Enhanced font analysis for question boundary detection.
    Identifies bold text which often indicates question starts.
    """
    font_name = context.current_block.font_name.lower()
    font_size = context.current_block.font_size
    
    # Expanded bold detection patterns
    is_bold = any(pattern in font_name for pattern in [
        'bold', 'black', 'heavy', 'extra', 'ultra', 'demi'
    ])
    
    # Check if font size is significantly larger than median
    median_font_size = getattr(context, 'scope_median_font_size', 12)
    is_large_font = font_size > median_font_size * 1.1
    
    # Determine confidence for question boundary detection
    confidence = "low"
    question_indicator = False
    
    if is_bold and is_large_font:
        confidence = "high"
        question_indicator = True
    elif is_bold:
        confidence = "medium" 
        question_indicator = True
    elif is_large_font:
        confidence = "low"
        question_indicator = True
    
    return {
        "heuristic_name": "font_style",
        "is_bold": is_bold,
        "is_large_font": is_large_font,
        "font_size": font_size,
        "median_font_size": median_font_size,
        "question_indicator": question_indicator,
        "confidence": confidence
    }