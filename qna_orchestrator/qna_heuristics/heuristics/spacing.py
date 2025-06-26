# in heuristics/spacing.py
from typing import Dict, Any, Optional
from qna_orchestrator.qna_heuristics.data_models import AnalysisContext

def analyze_vertical_break(context: AnalysisContext) -> Optional[Dict[str, Any]]:
    """
    Enhanced vertical break analysis with multiple gap threshold levels
    and context-aware detection for better question boundary identification
    """
    if not context.previous_block:
        return {"heuristic_name": "vertical_break", "is_break": False, "gap_size": 0, "break_type": "none"}

    cfg = context.config['HEURISTICS']['SPACING']
    gap = context.current_block.bbox[1] - context.previous_block.bbox[3]
    median_spacing = context.scope_median_spacing
    
    # Define multiple threshold levels for different break types
    small_break_mult = cfg.get('SMALL_BREAK_MULTIPLIER', 1.2)
    medium_break_mult = cfg.get('MEDIUM_BREAK_MULTIPLIER', 1.7)  # original
    large_break_mult = cfg.get('LARGE_BREAK_MULTIPLIER', 2.5)
    
    # Classify gap type
    break_type = "none"
    is_break = False
    
    if gap > (median_spacing * large_break_mult):
        break_type = "large_break"
        is_break = True
    elif gap > (median_spacing * medium_break_mult):
        break_type = "medium_break" 
        is_break = True
    elif gap > (median_spacing * small_break_mult):
        break_type = "small_break"
        is_break = True
    
    # Additional context: check if this might be a question boundary
    # Large gaps often indicate new questions, especially combined with other signals
    confidence = "low"
    if break_type == "large_break":
        confidence = "high"
    elif break_type == "medium_break":
        confidence = "medium"
    
    return {
        "heuristic_name": "vertical_break",
        "is_break": is_break,
        "break_type": break_type,
        "gap_size": round(gap, 2),
        "median_spacing": round(median_spacing, 2),
        "confidence": confidence
    }