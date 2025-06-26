import statistics
import re
from typing import List, Dict, Optional

from .pdf_parser import TextBlock


def is_bold(font_name: str) -> bool:
    """Checks if a font name suggests it is bold."""
    return 'bold' in font_name.lower() or 'black' in font_name.lower()

def starts_with_bold_question_intro(block: TextBlock, next_block: Optional[TextBlock]) -> bool:
    """Heuristic to check if a question starts with a specific bold phrase."""
    if is_bold(block.font_name) and "Consider the following statements:" in block.text:
        return True
    return False

def has_significant_space_before(block: TextBlock, prev_block: Optional[TextBlock], normal_spacing: float) -> bool:
    """Checks if there is a larger than usual vertical gap before a text block."""
    if not prev_block:
        return True  # First block on a page is a potential start

    gap = block.bbox[1] - prev_block.bbox[3]
    spacing_threshold = normal_spacing * 1.5  # Heuristic: 50% larger than normal
    return gap > spacing_threshold

def calculate_normal_spacing(blocks: List[TextBlock]) -> float:
    """Calculates the normal (median) line spacing for a list of blocks."""
    gaps = []
    if len(blocks) < 2:
        return 5.0  # Default spacing

    for i in range(1, len(blocks)):
        prev_block = blocks[i-1]
        curr_block = blocks[i]
        # Only consider blocks in the same column
        if abs(prev_block.bbox[0] - curr_block.bbox[0]) < 50:
            gap = curr_block.bbox[1] - prev_block.bbox[3]
            # Only consider positive, reasonable gaps for line spacing
            if 0 < gap < (prev_block.font_size * 3):
                gaps.append(gap)
    
    return statistics.median(gaps) if gaps else 5.0

def is_answer_start(block: TextBlock) -> bool:
    """Checks if a block starts with 'Ans:'"""
    return block.text.strip().lower().startswith('ans:')
