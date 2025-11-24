"""
PyMuPDF Text Extraction Strategy

Extracts text blocks from PDF files using PyMuPDF (fitz) library.
This is the default extraction strategy that provides good performance
and accurate text positioning.
"""

import fitz
from typing import List, Tuple, Dict, Any

from ..extraction import RawTextBlock


class PyMuPDFExtractor:
    """
    Text extraction strategy using PyMuPDF (fitz).
    
    This extractor processes PDF files at the line level, extracting text
    with positional and styling information (font size, font name, bounding box).
    
    Features:
    - Line-level extraction for accurate positioning
    - Font metadata preservation
    - Sorted in reading order (top-to-bottom, left-to-right)
    - Empty lines filtered out
    
    Example:
        extractor = PyMuPDFExtractor(config)
        blocks = extractor.extract_blocks("document.pdf", 0)
        width, height = extractor.get_page_dimensions("document.pdf", 0)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the PyMuPDF extractor.
        
        Args:
            config: Configuration dictionary (unused currently, reserved for future options)
        """
        self.config = config
    
    def extract_blocks(self, pdf_path: str, page_num: int) -> List[RawTextBlock]:
        """
        Extract text blocks from a specific page.
        
        Args:
            pdf_path: Path to the PDF file
            page_num: Page number (0-indexed)
            
        Returns:
            List of RawTextBlock objects sorted in reading order
        """
        doc = fitz.open(pdf_path)
        
        try:
            page = doc[page_num]
            blocks = self._extract_from_page(page, page_num)
            return blocks
        finally:
            doc.close()
    
    def get_page_dimensions(self, pdf_path: str, page_num: int) -> Tuple[float, float]:
        """
        Get the width and height of a specific page.
        
        Args:
            pdf_path: Path to the PDF file
            page_num: Page number (0-indexed)
            
        Returns:
            Tuple of (width, height) in points
        """
        doc = fitz.open(pdf_path)
        
        try:
            page = doc[page_num]
            return (page.rect.width, page.rect.height)
        finally:
            doc.close()
    
    def get_page_count(self, pdf_path: str) -> int:
        """
        Get the total number of pages in the PDF.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Total page count
        """
        doc = fitz.open(pdf_path)
        
        try:
            return len(doc)
        finally:
            doc.close()
    
    def _extract_from_page(self, page: fitz.Page, page_num: int) -> List[RawTextBlock]:
        """
        Internal method to extract blocks from a fitz Page object.
        
        Args:
            page: fitz.Page object
            page_num: Page number (0-indexed)
            
        Returns:
            List of RawTextBlock objects
        """
        raw_blocks = page.get_text("dict")["blocks"]
        text_blocks = []
        
        # Load noise patterns from config
        noise_patterns = self.config.get("NOISE_PATTERNS", [])
        
        for block in raw_blocks:
            if "lines" not in block:
                continue
            
            for line in block["lines"]:
                if not line["spans"]:
                    continue
                
                # Aggregate span information
                line_text = ""
                max_font_size = 0
                font_name = ""
                
                for span in line["spans"]:
                    line_text += span["text"]
                    max_font_size = max(max_font_size, span.get("size", 0))
                    if not font_name:
                        font_name = span.get("font", "Unknown")
                
                # Filter empty lines
                text = line_text.strip()
                if not text:
                    continue
                
                # --- NOISE FILTERING ---
                # Check if text contains any noise pattern (case insensitive)
                is_noise = False
                for pattern in noise_patterns:
                    if pattern.lower() in text.lower():
                        is_noise = True
                        break
                
                if is_noise:
                    continue
                # ----------------------------
                
                text_blocks.append(RawTextBlock(
                    text=text,
                    bbox=tuple(line["bbox"]),
                    font_size=max_font_size,
                    font_name=font_name,
                    page_number=page_num + 1  # 1-indexed for users
                ))
        
        # Sort by reading order: top-to-bottom, left-to-right
        text_blocks.sort(key=lambda b: (b.y0, b.x0))
        
        return text_blocks
