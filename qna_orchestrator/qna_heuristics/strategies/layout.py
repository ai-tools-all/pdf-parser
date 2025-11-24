"""
Layout Detection Strategy Interface

Defines how document layout is detected and blocks are classified
into regions (columns, headers, footers, etc.).
"""

from typing import Protocol, List, Dict, Any, Optional
from dataclasses import dataclass, field

from ..data_models import Page, TextBlock
from .extraction import RawTextBlock


@dataclass
class LayoutInfo:
    """
    Layout metadata detected from a page.
    
    Contains information about page structure such as column boundaries,
    reading regions, header/footer areas, etc.
    """
    # Column information
    column_count: int = 1
    column_separators: List[float] = field(default_factory=list)  # X-coordinates
    
    # Region boundaries (as fractions of page height)
    header_boundary: float = 0.1  # Top 10% is header
    footer_boundary: float = 0.9  # Bottom 10% is footer
    
    # Additional layout metadata
    detected_layout_type: str = "unknown"  # e.g., "two_column", "single_column"
    confidence: float = 1.0  # Confidence in layout detection (0-1)
    metadata: Dict[str, Any] = field(default_factory=dict)  # Extra info
    
    def get_column_index(self, x: float) -> int:
        """
        Determine which column an x-coordinate belongs to.
        
        Args:
            x: X-coordinate
            
        Returns:
            Column index (0-based)
        """
        if self.column_count == 1:
            return 0
        
        for i, separator in enumerate(self.column_separators):
            if x < separator:
                return i
        return len(self.column_separators)
    
    def is_in_header(self, y: float, page_height: float) -> bool:
        """Check if y-coordinate is in header region."""
        return y < (page_height * self.header_boundary)
    
    def is_in_footer(self, y: float, page_height: float) -> bool:
        """Check if y-coordinate is in footer region."""
        return y > (page_height * self.footer_boundary)
    
    def is_in_main_content(self, y: float, page_height: float) -> bool:
        """Check if y-coordinate is in main content region."""
        return not (self.is_in_header(y, page_height) or self.is_in_footer(y, page_height))


class LayoutDetectionStrategy(Protocol):
    """
    Protocol for layout detection strategies.
    
    Implementations define how to detect document layout and classify
    text blocks into regions (columns, headers, footers, etc.).
    
    Examples:
    - TwoColumnLayoutDetector: Detects 2-column layouts with dynamic separator
    - SingleColumnLayoutDetector: Simple top-to-bottom layout
    - VisionLayoutDetector: Uses ML models for complex layouts
    
    Usage:
        detector = TwoColumnLayoutDetector(config)
        layout_info = detector.detect_layout(page, raw_blocks)
        detector.classify_blocks(page, text_blocks, layout_info)
    """
    
    def detect_layout(self, page: Page, blocks: List[RawTextBlock]) -> LayoutInfo:
        """
        Analyze page structure and detect layout.
        
        Args:
            page: Page object with dimensions
            blocks: Raw text blocks extracted from the page
            
        Returns:
            LayoutInfo object containing detected layout metadata
            
        Note:
            - This method should analyze block positions, gaps, and patterns
            - It should NOT modify the blocks or page objects
            - The returned LayoutInfo guides block classification
        """
        ...
    
    def classify_blocks(
        self,
        page: Page,
        blocks: List[RawTextBlock],
        layout_info: LayoutInfo
    ) -> None:
        """
        Classify raw text blocks into page regions.
        
        Args:
            page: Page object to populate with classified blocks
            blocks: Raw text blocks to classify
            layout_info: Layout metadata from detect_layout()
            
        Side Effects:
            - Populates page.left_column_blocks
            - Populates page.right_column_blocks
            - Populates page.other_blocks (headers, footers)
            - Sets page.raw_left_text and page.raw_right_text
            
        Note:
            - Creates TextBlock objects from RawTextBlock with unique IDs
            - Blocks are assigned to regions based on layout_info
            - Maintains reading order within each region
        """
        ...
