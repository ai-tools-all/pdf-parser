"""
Concrete implementations of parser strategies.

This package contains ready-to-use implementations of the strategy interfaces:
- Text extraction strategies (PyMuPDF, pdfplumber, etc.)
- Layout detection strategies (2-column, single-column, etc.)
- Heuristic analysis strategies (default, aggressive, conservative)
- OCR providers (PaddleOCR, OpenAI Vision API)
"""

from .pymupdf_extractor import PyMuPDFExtractor
from .two_column_layout import TwoColumnLayoutDetector
from .default_heuristic_analyzer import DefaultHeuristicAnalyzer

# Register OCR providers (lazy import - actual provider loading happens on use)
def _register_ocr_providers():
    """Register available OCR providers."""
    from ..ocr import OCRProviderRegistry
    
    # Try to register PaddleOCR provider
    try:
        from .paddle_ocr_provider import PaddleOCRProvider
        OCRProviderRegistry.register("paddle", PaddleOCRProvider)
    except ImportError:
        pass  # PaddleOCR not installed
    
    # Try to register OpenAI provider
    try:
        from .openai_ocr_provider import OpenAIOCRProvider
        OCRProviderRegistry.register("openai", OpenAIOCRProvider)
    except ImportError:
        pass  # OpenAI not installed

_register_ocr_providers()

__all__ = [
    'PyMuPDFExtractor',
    'TwoColumnLayoutDetector',
    'DefaultHeuristicAnalyzer',
]
