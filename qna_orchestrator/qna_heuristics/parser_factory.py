"""
Parser Factory

Provides convenient constructors for creating parsers with common configurations.
Allows easy creation of custom parsers by injecting different strategies.
"""

from typing import Dict, Any, Optional

from .composable_parser import ComposableParser
from .strategies import (
    TextExtractionStrategy,
    LayoutDetectionStrategy,
    HeuristicAnalysisStrategy,
)
from .strategies.implementations import (
    PyMuPDFExtractor,
    TwoColumnLayoutDetector,
    DefaultHeuristicAnalyzer,
)


class ParserFactory:
    """
    Factory for creating PDF parsers with different configurations.
    
    This factory provides:
    1. Default parser (current PDFParser behavior)
    2. Custom parser creation by injecting strategies
    
    Usage:
        # Use default configuration
        parser = ParserFactory.create_default(config)
        
        # Or inject custom strategies
        parser = ParserFactory.create_custom(
            extraction=MyCustomExtractor(config),
            layout=TwoColumnLayoutDetector(config),
            analysis=DefaultHeuristicAnalyzer(config),
            config=config
        )
    """
    
    @staticmethod
    def create_default(config: Dict[str, Any]) -> ComposableParser:
        """
        Create parser with default strategies (current PDFParser behavior).
        
        Uses:
        - PyMuPDFExtractor for text extraction
        - TwoColumnLayoutDetector for layout
        - DefaultHeuristicAnalyzer for heuristics
        
        Args:
            config: Configuration dictionary
            
        Returns:
            ComposableParser with default strategies
            
        Example:
            config = get_config()
            parser = ParserFactory.create_default(config)
            document = parser.parse("exam.pdf")
        """
        return ComposableParser(
            extraction_strategy=PyMuPDFExtractor(config),
            layout_strategy=TwoColumnLayoutDetector(config),
            analysis_strategy=DefaultHeuristicAnalyzer(config),
            config=config
        )
    
    @staticmethod
    def create_custom(
        extraction: TextExtractionStrategy,
        layout: LayoutDetectionStrategy,
        analysis: HeuristicAnalysisStrategy,
        config: Dict[str, Any]
    ) -> ComposableParser:
        """
        Create parser with custom strategies.
        
        This allows full control over parser behavior by injecting
        custom strategy implementations.
        
        Args:
            extraction: Text extraction strategy
            layout: Layout detection strategy
            analysis: Heuristic analysis strategy
            config: Configuration dictionary
            
        Returns:
            ComposableParser with custom strategies
            
        Example:
            parser = ParserFactory.create_custom(
                extraction=PDFPlumberExtractor(config),
                layout=SingleColumnLayoutDetector(config),
                analysis=AggressiveHeuristicAnalyzer(config),
                config=config
            )
        """
        return ComposableParser(
            extraction_strategy=extraction,
            layout_strategy=layout,
            analysis_strategy=analysis,
            config=config
        )
