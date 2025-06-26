# in heuristics/spacing.py
from typing import Dict, Any, Optional
from qna_orchestrator.qna_heuristics.data_models import AnalysisContext

def analyze_vertical_break(context: AnalysisContext) -> Optional[Dict[str, Any]]:
    """Identifies if a block is preceded by a large vertical gap."""
    if not context.previous_block:
        return None

    cfg = context.config['HEURISTICS']['SPACING']
    gap = context.current_block.bbox[1] - context.previous_block.bbox[3]
    multiplier = cfg['BREAK_THRESHOLD_MULTIPLIER']
    
    # Use pre-calculated median spacing for efficiency
    median_spacing = context.scope_median_spacing

    if gap > (median_spacing * multiplier):
        return {
            "heuristic_name": "vertical_break",
            "is_break": True,
            "gap_size": round(gap, 2)
        }
    return None