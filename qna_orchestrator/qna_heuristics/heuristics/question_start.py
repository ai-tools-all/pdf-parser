
from typing import Optional, Dict, Any
import re
from ..data_models import AnalysisContext

def is_question_start(context: AnalysisContext) -> Optional[Dict[str, Any]]:
    """
    A dedicated heuristic to detect the start of a question.
    """
    block = context.current_block
    prev_block = context.previous_block

    # Check for a question number at the beginning of the block
    match = re.match(r'^(\d+)\.\s+', block.text)
    if not match:
        return None

    question_number = int(match.group(1))

    # Check for bold font
    font_style_analysis = next((r for r in block.analysis_results if r.get("heuristic_name") == "font_style"), None)
    is_bold = font_style_analysis and font_style_analysis.get("is_bold", False)

    # Check for vertical space
    layout_analysis = next((r for r in block.analysis_results if r.get("heuristic_name") == "layout_analysis"), None)
    is_significant_space = False
    if layout_analysis:
        if layout_analysis.get("is_first_block"):
            is_significant_space = True
        elif layout_analysis.get("vertical_gap_from_prev", 0) > 8:
            is_significant_space = True

    if is_significant_space:
        return {
            "heuristic_name": "question_start",
            "is_question_start": True,
            "question_number": question_number
        }

    return None
