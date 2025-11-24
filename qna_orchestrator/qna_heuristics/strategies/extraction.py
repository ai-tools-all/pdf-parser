"""
Text Extraction Strategy Interface

Defines how raw text and metadata are extracted from PDF documents.
Different implementations can use PyMuPDF, pdfplumber, LayoutLM, etc.
"""

from typing import Protocol, List, Tuple
from dataclasses import dataclass


@dataclass
class RawTextBlock:
    """
    Raw text block extracted from PDF before layout classification.
    
    This is a pre-processing data structure that contains minimal
    information about text position and styling.
    """
    text: str
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1)
    font_size: float
    font_name: str
    page_number: int
    
    @property
    def x0(self) -> float:
        return self.bbox[0]
    
    @property
    def y0(self) -> float:
        return self.bbox[1]
    
    @property
    def x1(self) -> float:
        return self.bbox[2]
    
    @property
    def y1(self) -> float:
        return self.bbox[3]
    
    @property
    def center_x(self) -> float:
        return (self.bbox[0] + self.bbox[2]) / 2
    
    @property
    def center_y(self) -> float:
        return (self.bbox[1] + self.bbox[3]) / 2
    
    @property
    def width(self) -> float:
        return self.bbox[2] - self.bbox[0]
    
    @property
    def height(self) -> float:
        return self.bbox[3] - self.bbox[1]


class TextExtractionStrategy(Protocol):
    """
    Protocol for text extraction strategies.
    
    Implementations define how to extract raw text blocks from PDF files.
    Examples:
    - PyMuPDFExtractor: Uses fitz (PyMuPDF) for extraction
    - PDFPlumberExtractor: Uses pdfplumber for better table handling
    - LayoutLMExtractor: Uses vision models for complex layouts
    
    Usage:
        extractor = PyMuPDFExtractor(config)
        page_count = extractor.get_page_count("document.pdf")
        for page_num in range(page_count):
            blocks = extractor.extract_blocks("document.pdf", page_num)
            width, height = extractor.get_page_dimensions("document.pdf", page_num)
    """
    
    def extract_blocks(self, pdf_path: str, page_num: int) -> List[RawTextBlock]:
        """
        Extract raw text blocks from a specific page.
        
        Args:
            pdf_path: Path to the PDF file
            page_num: Page number (0-indexed)
            
        Returns:
            List of RawTextBlock objects containing text and metadata
            
        Note:
            - Blocks should be sorted in reading order (top-to-bottom, left-to-right)
            - Empty text blocks should be filtered out
            - Font information should be preserved when available
        """
        ...
    
    def get_page_dimensions(self, pdf_path: str, page_num: int) -> Tuple[float, float]:
        """
        Get the width and height of a specific page.
        
        Args:
            pdf_path: Path to the PDF file
            page_num: Page number (0-indexed)
            
        Returns:
            Tuple of (width, height) in points
        """
        ...
    
    def get_page_count(self, pdf_path: str) -> int:
        """
        Get the total number of pages in the PDF.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Total page count
        """
        ...
