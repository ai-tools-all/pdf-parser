"""
Composable Parser Implementation

A flexible parser that uses strategy pattern to compose different
extraction, layout detection, and analysis approaches.
"""

from typing import Dict, Any
from copy import deepcopy

from .data_models import Document, Page, TextBlock
from .strategies import (
    TextExtractionStrategy,
    LayoutDetectionStrategy,
    HeuristicAnalysisStrategy,
    RawTextBlock,
)


class ComposableParser:
    """
    A composable PDF parser that uses pluggable strategies.
    
    This parser separates concerns into three main strategies:
    1. TextExtractionStrategy: How to extract raw text from PDFs
    2. LayoutDetectionStrategy: How to detect and classify layout
    3. HeuristicAnalysisStrategy: How to analyze content semantically
    
    Example:
        parser = ComposableParser(
            extraction_strategy=PyMuPDFExtractor(config),
            layout_strategy=TwoColumnLayoutDetector(config),
            analysis_strategy=DefaultHeuristicAnalyzer(config),
            config=config
        )
        doc = parser.parse("exam.pdf")
    
    Attributes:
        extraction: Strategy for extracting text from PDFs
        layout: Strategy for detecting and classifying layout
        analysis: Strategy for applying heuristics
        config: Configuration dictionary
    """
    
    def __init__(
        self,
        extraction_strategy: TextExtractionStrategy,
        layout_strategy: LayoutDetectionStrategy,
        analysis_strategy: HeuristicAnalysisStrategy,
        config: Dict[str, Any]
    ):
        """
        Initialize the composable parser with strategies.
        
        Args:
            extraction_strategy: How to extract text blocks
            layout_strategy: How to detect layout
            analysis_strategy: How to apply heuristics
            config: Configuration dictionary
        """
        self.extraction = extraction_strategy
        self.layout = layout_strategy
        self.analysis = analysis_strategy
        self.config = deepcopy(config)
    
    def parse(self, pdf_path: str) -> Document:
        """
        Parse a PDF document using the configured strategies.
        
        This method orchestrates the three-phase parsing process:
        1. Extract raw text blocks from each page
        2. Detect layout and classify blocks into regions
        3. Analyze blocks with heuristics
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Document object with parsed and analyzed pages
            
        Process:
            For each page:
                1. Extract raw blocks (extraction strategy)
                2. Detect layout structure (layout strategy)
                3. Classify blocks into regions (layout strategy)
                4. Apply heuristics to each region (analysis strategy)
        """
        doc = Document(pdf_path=pdf_path)
        
        # Get total page count
        page_count = self.extraction.get_page_count(pdf_path)
        
        for page_num in range(page_count):
            # Phase 1: Extract raw text blocks
            raw_blocks = self.extraction.extract_blocks(pdf_path, page_num)
            width, height = self.extraction.get_page_dimensions(pdf_path, page_num)
            
            # Create page object
            page = Page(
                page_number=page_num + 1,  # 1-indexed for users
                page_width=width,
                page_height=height,
            )
            
            # Phase 2: Detect layout structure
            layout_info = self.layout.detect_layout(page, raw_blocks)
            
            # Phase 3: Classify blocks into regions
            self.layout.classify_blocks(page, raw_blocks, layout_info)
            
            # Phase 4: Analyze each region with heuristics
            if page.left_column_blocks:
                self.analysis.analyze_blocks(
                    page.left_column_blocks,
                    page,
                    self.config
                )
            
            if page.right_column_blocks:
                self.analysis.analyze_blocks(
                    page.right_column_blocks,
                    page,
                    self.config
                )
            
            # Note: We don't analyze other_blocks (headers/footers)
            # as they typically don't contain MCQ content
            
            doc.pages.append(page)
        
        return doc
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"ComposableParser(\n"
            f"  extraction={self.extraction.__class__.__name__},\n"
            f"  layout={self.layout.__class__.__name__},\n"
            f"  analysis={self.analysis.__class__.__name__}\n"
            f")"
        )
