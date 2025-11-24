"""
Default Heuristic Analysis Strategy

Applies configurable heuristics to analyze document content.
Uses dynamic loading of heuristic functions from config.
"""

import statistics
import importlib
from typing import List, Dict, Any, Callable, Optional

from ...data_models import TextBlock, Page, AnalysisContext


class DefaultHeuristicAnalyzer:
    """
    Default heuristic analysis strategy.
    
    This analyzer:
    1. Loads heuristic functions from config paths
    2. Calculates scope-wide metrics (median spacing, font sizes, etc.)
    3. Applies each heuristic sequentially to blocks
    4. Populates block.analysis_results with findings
    
    Features:
    - Dynamic heuristic loading from config
    - Context-aware analysis (previous blocks inform current analysis)
    - Scope-wide metric calculation for consistent thresholds
    - Extensible via config changes
    
    Example:
        analyzer = DefaultHeuristicAnalyzer(config)
        analyzer.analyze_blocks(page.left_column_blocks, page, config)
        
        # Check results
        for block in page.left_column_blocks:
            print(block.analysis_results)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the default heuristic analyzer.
        
        Args:
            config: Configuration dictionary with ACTIVE_HEURISTICS list
        """
        self.config = config
        self.heuristics = self._load_heuristics()
    
    def analyze_blocks(
        self,
        blocks: List[TextBlock],
        page: Page,
        config: Dict[str, Any]
    ) -> None:
        """
        Analyze text blocks and populate their analysis_results.
        
        This method:
        1. Calculates scope-wide metrics (spacing, font sizes)
        2. Creates AnalysisContext for each block
        3. Applies each heuristic sequentially
        4. Accumulates results in block.analysis_results
        
        Args:
            blocks: List of TextBlock objects to analyze
            page: Page object containing context
            config: Configuration dictionary
            
        Side Effects:
            Populates block.analysis_results for each block
        """
        if not blocks:
            return
        
        # Calculate scope-wide metrics
        spacing_config = config.get('HEURISTICS', {}).get('SPACING', {})
        median_spacing = self._calculate_median_spacing(blocks, spacing_config)
        min_x = min(b.bbox[0] for b in blocks)
        median_font_size = self._calculate_median_font_size(blocks)
        
        # Apply heuristics to each block
        previous_analysis = None
        for i, block in enumerate(blocks):
            prev_block = blocks[i - 1] if i > 0 else None
            
            # Create analysis context
            context = AnalysisContext(
                current_block=block,
                previous_block=prev_block,
                all_blocks_in_scope=blocks,
                scope_median_spacing=median_spacing,
                scope_min_x=min_x,
                scope_median_font_size=median_font_size,
                config=config,
                page_data=page,
                previous_analysis=previous_analysis
            )
            
            # Apply each heuristic
            current_block_analysis = {}
            for heuristic_func in self.heuristics:
                result = heuristic_func(context)
                if result:
                    block.analysis_results.append(result)
                    current_block_analysis.update(result)
            
            previous_analysis = current_block_analysis
    
    def get_heuristics(self) -> List[Callable]:
        """
        Get the list of loaded heuristic functions.
        
        Returns:
            List of callable heuristic functions
        """
        return self.heuristics
    
    def _load_heuristics(self) -> List[Callable]:
        """
        Dynamically load heuristic functions from config paths.
        
        Returns:
            List of loaded heuristic functions
        """
        loaded_funcs = []
        heuristic_paths = self.config.get("ACTIVE_HEURISTICS", [])
        
        for path in heuristic_paths:
            module_path, func_name = path.rsplit('.', 1)
            try:
                module = importlib.import_module(module_path)
                func = getattr(module, func_name)
                loaded_funcs.append(func)
            except (ImportError, AttributeError) as e:
                print(f"Warning: Could not load heuristic '{path}': {e}")
        
        return loaded_funcs
    
    def _calculate_median_spacing(
        self,
        blocks: List[TextBlock],
        spacing_config: Dict[str, Any]
    ) -> float:
        """
        Calculate median vertical spacing between blocks.
        
        Filters out unusually small and large gaps to get
        a robust estimate of normal line spacing.
        
        Args:
            blocks: List of text blocks
            spacing_config: Spacing configuration
            
        Returns:
            Median spacing in points
        """
        if len(blocks) < 2:
            return 5.0  # Default
        
        min_gap = spacing_config.get('MIN_GAP_FOR_NORMAL_SPACING', 0.5)
        max_gap = spacing_config.get('MAX_GAP_FOR_NORMAL_SPACING', 20.0)
        
        gaps = []
        for i in range(1, len(blocks)):
            gap = blocks[i].bbox[1] - blocks[i - 1].bbox[3]
            if min_gap < gap < max_gap:
                gaps.append(gap)
        
        return statistics.median(gaps) if gaps else 5.0
    
    def _calculate_median_font_size(self, blocks: List[TextBlock]) -> float:
        """
        Calculate median font size across blocks.
        
        Args:
            blocks: List of text blocks
            
        Returns:
            Median font size in points
        """
        font_sizes = [b.font_size for b in blocks if b.font_size > 0]
        return statistics.median(font_sizes) if font_sizes else 12.0
