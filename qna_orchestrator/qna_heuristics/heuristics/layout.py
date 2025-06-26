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
    """Analyzes the font for properties like bold."""
    font_name = context.current_block.font_name.lower()
    is_bold = 'bold' in font_name or 'black' in font_name

    if is_bold:
        return {
            "heuristic_name": "font_style",
            "is_bold": True
        }
    return None