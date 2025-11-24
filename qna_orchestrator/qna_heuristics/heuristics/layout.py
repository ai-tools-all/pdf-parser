# in heuristics/layout.py
from typing import Dict, Any, Optional
from qna_orchestrator.qna_heuristics.data_models import AnalysisContext

def analyze_block_layout(context: AnalysisContext) -> Optional[Dict[str, Any]]:
    """
    Analyzes the spatial relationship of a block with its neighbors.
    """
    current_block = context.current_block
    prev_block = context.previous_block

    if not prev_block:
        return {
            "heuristic_name": "layout_analysis",
            "is_first_block": True,
            "vertical_gap_from_prev": None,
            "horizontal_alignment_with_prev": "N/A"
        }

    v_gap = current_block.bbox[1] - prev_block.bbox[3]
    h_gap = current_block.bbox[0] - prev_block.bbox[0]
    
    h_alignment = "aligned"
    if abs(h_gap) > 5:
        h_alignment = "indented" if h_gap > 0 else "outdented"

    return {
        "heuristic_name": "layout_analysis",
        "is_first_block": False,
        "vertical_gap_from_prev": round(v_gap, 2),
        "horizontal_gap_from_prev": round(h_gap, 2),
        "horizontal_alignment_with_prev": h_alignment
    }


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


def determine_reading_order(left_sorted, right_sorted, current_block):
    # This is a placeholder. A more sophisticated implementation would be needed
    # to handle complex layouts.
    if current_block in left_sorted:
        return left_sorted.index(current_block)
    elif current_block in right_sorted:
        return len(left_sorted) + right_sorted.index(current_block)
    return -1

def sequence_column_content(context: AnalysisContext) -> Optional[Dict]:
    """Ensure proper sequencing of two-column content"""
    
    # Get all blocks in current scope
    left_blocks = context.page_data.left_column_blocks if context.page_data else []
    right_blocks = context.page_data.right_column_blocks if context.page_data else []
    
    # Sort by vertical position within each column
    left_sorted = sorted(left_blocks, key=lambda b: b.bbox[1])
    right_sorted = sorted(right_blocks, key=lambda b: b.bbox[1])
    
    # Determine reading order based on vertical alignment
    current_block = context.current_block
    
    return {
        "heuristic_name": "column_sequencing",
        "column": "left" if current_block in left_blocks else "right",
        "reading_order": determine_reading_order(left_sorted, right_sorted, current_block),
        "confidence": 0.9
    }

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