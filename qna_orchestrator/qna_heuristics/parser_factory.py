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
    def create_from_config(config: Dict[str, Any], parser_name: Optional[str] = None) -> ComposableParser:
        """
        Create parser from configuration by name.

        Args:
            config: Full configuration dictionary
            parser_name: Name of parser config to use (defaults to DEFAULT_PARSER)

        Returns:
            Configured ComposableParser instance

        Example:
            config = get_config()
            parser = ParserFactory.create_from_config(config, "clustering_enhanced")
            document = parser.parse("exam.pdf")
        """
        if parser_name is None:
            parser_name = config.get("DEFAULT_PARSER", "default")

        parsers_config = config.get("PARSERS", {})
        parser_config = parsers_config.get(parser_name)

        if not parser_config:
            raise ValueError(f"Parser configuration '{parser_name}' not found")

        parser_type = parser_config.get("type", "composable")

        if parser_type == "heuristic_based":
            # Import here to avoid circular imports
            from .parsers import HeuristicBasedParser
            # Merge parser config into main config
            merged_config = {**config, **parser_config}
            return HeuristicBasedParser(merged_config)
        else:
            # Handle composable parsers
            analysis_strategy_name = parser_config.get("analysis", "default")
            analysis_strategies = config.get("ANALYSIS_STRATEGIES", {})
            analysis_config = analysis_strategies.get(analysis_strategy_name, {"ACTIVE_HEURISTICS": []})

            # Merge analysis config into main config
            merged_config = {**config, **analysis_config}

            # Create the analysis strategy
            analysis_strategy = DefaultHeuristicAnalyzer(merged_config)

            # Create extraction and layout strategies
            extraction_strategy = PyMuPDFExtractor(merged_config)
            layout_strategy = TwoColumnLayoutDetector(merged_config)

            return ComposableParser(
                extraction_strategy=extraction_strategy,
                layout_strategy=layout_strategy,
                analysis_strategy=analysis_strategy,
                config=merged_config
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
