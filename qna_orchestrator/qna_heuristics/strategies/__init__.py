"""
Strategy interfaces for composable PDF parsers.

This module defines the protocols (interfaces) for pluggable components
in the parser pipeline:
- TextExtractionStrategy: How to extract raw text from PDFs
- LayoutDetectionStrategy: How to detect document layout
- HeuristicAnalysisStrategy: How to apply content analysis heuristics
- OCRProvider: How to extract text from images (pluggable OCR backends)
"""

from .extraction import TextExtractionStrategy, RawTextBlock
from .layout import LayoutDetectionStrategy, LayoutInfo
from .analysis import HeuristicAnalysisStrategy
from .ocr import OCRProvider, OCRResult, OCRProviderRegistry, get_ocr_provider

__all__ = [
    'TextExtractionStrategy',
    'RawTextBlock',
    'LayoutDetectionStrategy',
    'LayoutInfo',
    'HeuristicAnalysisStrategy',
    'OCRProvider',
    'OCRResult',
    'OCRProviderRegistry',
    'get_ocr_provider',
]
