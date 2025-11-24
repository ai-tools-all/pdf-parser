"""
Heuristic Analysis Strategy Interface

Defines how heuristics are applied to analyze document content
and extract semantic information (questions, answers, options, etc.).
"""

from typing import Protocol, List, Callable, Dict, Any

from ..data_models import TextBlock, Page


class HeuristicAnalysisStrategy(Protocol):
    """
    Protocol for heuristic analysis strategies.
    
    Implementations define which heuristics to apply and how to
    orchestrate their execution on text blocks.
    
    Examples:
    - DefaultHeuristicAnalyzer: Uses config-based heuristic loading
    - AggressiveHeuristicAnalyzer: Applies many heuristics for maximum detection
    - ConservativeHeuristicAnalyzer: Uses minimal heuristics for high precision
    - CustomHeuristicAnalyzer: User-defined heuristic combinations
    
    Usage:
        analyzer = DefaultHeuristicAnalyzer(config)
        analyzer.analyze_blocks(page.left_column_blocks, page, config)
        
        # Or custom
        analyzer = CustomHeuristicAnalyzer([spacing_heuristic, question_start])
        analyzer.analyze_blocks(blocks, page, config)
    """
    
    def analyze_blocks(
        self,
        blocks: List[TextBlock],
        page: Page,
        config: Dict[str, Any]
    ) -> None:
        """
        Analyze text blocks and populate their analysis_results.
        
        Args:
            blocks: List of TextBlock objects to analyze
            page: Page object containing context
            config: Configuration dictionary
            
        Side Effects:
            - Populates block.analysis_results for each block
            - Each heuristic appends its findings to analysis_results
            - Analysis results are dictionaries with heuristic metadata
            
        Note:
            - This method orchestrates multiple heuristics
            - Heuristics should be applied in a consistent order
            - Context from previous blocks may inform later analysis
            
        Example analysis_results structure:
            [
                {
                    "heuristic_name": "spacing",
                    "has_large_gap_before": True,
                    "gap_size": 15.5
                },
                {
                    "heuristic_name": "question_start",
                    "is_question_start": True,
                    "question_number": 42
                }
            ]
        """
        ...
    
    def get_heuristics(self) -> List[Callable]:
        """
        Get the list of heuristic functions used by this strategy.
        
        Returns:
            List of callable heuristic functions
            
        Note:
            - Each heuristic should accept AnalysisContext and return Dict or None
            - The order matters - heuristics are applied sequentially
            - Useful for introspection and debugging
        """
        ...
