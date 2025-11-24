# in data_models.py
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional

@dataclass
class TextBlock:
    id: str  # e.g., "p1-b23"
    page_number: int
    text: str
    bbox: Tuple[float, float, float, float]
    font_size: float
    font_name: str
    # This list will be populated by the analysis phase
    analysis_results: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class Page:
    page_number: int
    page_width: float
    page_height: float
    left_column_blocks: List[TextBlock] = field(default_factory=list)
    right_column_blocks: List[TextBlock] = field(default_factory=list)
    other_blocks: List[TextBlock] = field(default_factory=list) # Header, footer, etc.
    # Raw content is preserved here for inspection
    raw_left_text: str = ""
    raw_right_text: str = ""

@dataclass
class Document:
    pdf_path: str
    pages: List[Page] = field(default_factory=list)

@dataclass
class MCQ:
    question_number: int
    question_text: str
    options: Dict[str, str] = field(default_factory=dict)
    answer: Optional[str] = None
    explanation: Optional[str] = None

class AnalysisContext:
    """Provides a heuristic with surrounding information."""
    def __init__(
        self,
        current_block: TextBlock,
        previous_block: Optional[TextBlock],
        all_blocks_in_scope: List[TextBlock],
        scope_median_spacing: float,
        scope_min_x: float,
        scope_median_font_size: float,
        config: Dict[str, Any],
        page_data: Optional[Page] = None,
        previous_analysis: Optional[Dict[str, Any]] = None
    ):
        self.current_block = current_block
        self.previous_block = previous_block
        self.all_blocks_in_scope = all_blocks_in_scope
        self.scope_median_spacing = scope_median_spacing
        self.scope_min_x = scope_min_x
        self.scope_median_font_size = scope_median_font_size
        self.config = config
        self.page_data = page_data
        self.previous_analysis = previous_analysis