# in heuristics/layout.py
from typing import Dict, Any, Optional
from data_models import AnalysisContext

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