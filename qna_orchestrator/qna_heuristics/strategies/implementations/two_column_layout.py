"""
Two-Column Layout Detection Strategy

Detects and classifies text blocks in 2-column PDF layouts.
Uses dynamic column separator detection based on text distribution.
"""

from typing import List, Dict, Any

from ..layout import LayoutInfo
from ..extraction import RawTextBlock
from ...data_models import Page, TextBlock


class TwoColumnLayoutDetector:
    """
    Layout detection strategy for 2-column documents.
    
    This strategy:
    1. Analyzes text distribution to find the column separator
    2. Detects header and footer regions
    3. Classifies blocks into left column, right column, or other (header/footer)
    
    Features:
    - Dynamic column separator detection (no hardcoded positions)
    - Handles varying column widths
    - Configurable header/footer boundaries
    - Falls back to center if no clear separator found
    
    Example:
        detector = TwoColumnLayoutDetector(config)
        layout_info = detector.detect_layout(page, raw_blocks)
        detector.classify_blocks(page, raw_blocks, layout_info)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the two-column layout detector.
        
        Args:
            config: Configuration dictionary with PARSER section containing:
                - HEADER_REGION_PERCENT: Fraction of page height for header (e.g., 0.1 = top 10%)
                - FOOTER_REGION_PERCENT: Fraction of page height for footer (e.g., 0.9 = bottom 10%)
        """
        self.config = config
        parser_config = config.get("PARSER", {})
        self.header_percent = parser_config.get("HEADER_REGION_PERCENT", 0.1)
        self.footer_percent = parser_config.get("FOOTER_REGION_PERCENT", 0.9)
    
    def detect_layout(self, page: Page, blocks: List[RawTextBlock]) -> LayoutInfo:
        """
        Detect 2-column layout structure by finding the column separator.
        
        Args:
            page: Page object with dimensions
            blocks: Raw text blocks extracted from the page
            
        Returns:
            LayoutInfo with column separator and region boundaries
        """
        separator_x = self._find_column_separator(page, blocks)
        
        layout_info = LayoutInfo(
            column_count=2,
            column_separators=[separator_x],
            header_boundary=self.header_percent,
            footer_boundary=self.footer_percent,
            detected_layout_type="two_column",
            confidence=1.0,  # Could be enhanced with confidence scoring
            metadata={
                "separator_x": separator_x,
                "page_width": page.page_width,
                "page_height": page.page_height
            }
        )
        
        return layout_info
    
    def classify_blocks(
        self,
        page: Page,
        blocks: List[RawTextBlock],
        layout_info: LayoutInfo
    ) -> None:
        """
        Classify raw text blocks into page regions.
        
        Args:
            page: Page object to populate
            blocks: Raw text blocks to classify
            layout_info: Layout metadata from detect_layout()
            
        Side Effects:
            Populates page.left_column_blocks, page.right_column_blocks,
            page.other_blocks, and raw text fields
        """
        separator_x = layout_info.column_separators[0] if layout_info.column_separators else page.page_width / 2
        header_y = page.page_height * layout_info.header_boundary
        footer_y = page.page_height * layout_info.footer_boundary
        
        block_id = 0
        for raw_block in blocks:
            # Create TextBlock with unique ID
            text_block = TextBlock(
                id=f"p{raw_block.page_number}-b{block_id}",
                page_number=raw_block.page_number,
                text=raw_block.text,
                bbox=raw_block.bbox,
                font_size=raw_block.font_size,
                font_name=raw_block.font_name
            )
            block_id += 1
            
            # Classify based on position
            center_y = raw_block.center_y
            center_x = raw_block.center_x
            
            if center_y < header_y or center_y > footer_y:
                # Header or footer region
                page.other_blocks.append(text_block)
            elif center_x < separator_x:
                # Left column
                page.left_column_blocks.append(text_block)
            else:
                # Right column
                page.right_column_blocks.append(text_block)
        
        # Generate raw text for inspection
        page.raw_left_text = "\n".join(b.text for b in page.left_column_blocks)
        page.raw_right_text = "\n".join(b.text for b in page.right_column_blocks)
    
    def _find_column_separator(self, page: Page, blocks: List[RawTextBlock]) -> float:
        """
        Find dynamic column separator by analyzing text distribution.
        
        Strategy:
        1. Collect x-coordinates from all blocks (left, center, right edges)
        2. Sort coordinates and find gaps
        3. Find the largest gap in the middle 60% of the page
        4. Use the center of that gap as the separator
        
        Args:
            page: Page object with dimensions
            blocks: Raw text blocks
            
        Returns:
            X-coordinate of the column separator
        """
        if not blocks:
            return page.page_width / 2
        
        # Collect x-coordinates
        x_coords = []
        for block in blocks:
            x_coords.extend([block.x0, block.center_x, block.x1])
        
        x_coords.sort()
        page_width = page.page_width
        
        # Search for largest gap in middle region
        start_range = page_width * 0.2  # Skip leftmost 20%
        end_range = page_width * 0.8    # Skip rightmost 20%
        min_gap_size = page_width * 0.05  # Minimum 5% of page width
        
        largest_gap = 0
        best_separator = page_width / 2  # Fallback to center
        
        for i in range(len(x_coords) - 1):
            gap_start = x_coords[i]
            gap_end = x_coords[i + 1]
            gap_size = gap_end - gap_start
            gap_center = (gap_start + gap_end) / 2
            
            # Only consider gaps in the middle region
            if (start_range <= gap_center <= end_range and 
                gap_size > largest_gap and 
                gap_size > min_gap_size):
                largest_gap = gap_size
                best_separator = gap_center
        
        return best_separator
