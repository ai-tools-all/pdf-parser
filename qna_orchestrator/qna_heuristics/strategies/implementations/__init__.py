"""
Concrete implementations of parser strategies.

This package contains ready-to-use implementations of the strategy interfaces:
- Text extraction strategies (PyMuPDF, pdfplumber, etc.)
- Layout detection strategies (2-column, single-column, etc.)
- Heuristic analysis strategies (default, aggressive, conservative)
"""

from .pymupdf_extractor import PyMuPDFExtractor
from .two_column_layout import TwoColumnLayoutDetector
from .default_heuristic_analyzer import DefaultHeuristicAnalyzer

__all__ = [
    'PyMuPDFExtractor',
    'TwoColumnLayoutDetector',
    'DefaultHeuristicAnalyzer',
]
