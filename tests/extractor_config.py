"""
Configuration mapping PDFs to their appropriate extractor implementations.

This file defines which extractor should be used for each PDF file.
This allows different PDFs to use different extraction strategies while
maintaining the same testing code.

Usage:
    from extractor_config import get_extractor_for_pdf

    extractor_class = get_extractor_for_pdf("academic_paper.pdf")
    result = extract_with_implementation(
        pdf_path="data/academic_paper.pdf",
        pages=1,
        extractor_class=extractor_class
    )
"""

from typing import Dict, Type, Optional
from pathlib import Path

# Import available extractors
from A003_colored_footer import PDFColumnExtractor

# You can import other extractors as they become available
# from A002_header_footer_2_col import SimpleExtractor
# from custom_extractor import CustomExtractor


# PDF -> Extractor mapping
# Key: PDF filename (without path)
# Value: Extractor class to use
EXTRACTOR_MAP: Dict[str, Type] = {
    # Example mappings - update these based on your test PDFs
    "document.pdf": PDFColumnExtractor,

    # Add more mappings as needed:
    # "academic_paper.pdf": PDFColumnExtractor,
    # "simple_doc.pdf": SimpleExtractor,
    # "complex_layout.pdf": CustomExtractor,
}


# Default extractor to use when PDF is not in the map
DEFAULT_EXTRACTOR = PDFColumnExtractor


def get_extractor_for_pdf(
    pdf_path: str,
    default: Optional[Type] = None
) -> Type:
    """
    Get the appropriate extractor class for a PDF file.

    Args:
        pdf_path: Path to the PDF file (can be full path or just filename)
        default: Optional default extractor to use if PDF not in map.
                 If None, uses DEFAULT_EXTRACTOR.

    Returns:
        Extractor class to use for this PDF

    Example:
        >>> extractor = get_extractor_for_pdf("document.pdf")
        >>> print(extractor.__name__)
        'PDFColumnExtractor'
    """
    # Extract filename from path
    filename = Path(pdf_path).name

    # Look up in map
    if filename in EXTRACTOR_MAP:
        return EXTRACTOR_MAP[filename]

    # Use default
    if default is not None:
        return default

    return DEFAULT_EXTRACTOR


def register_extractor(pdf_filename: str, extractor_class: Type):
    """
    Register a new PDF -> Extractor mapping.

    Useful for dynamic configuration or testing.

    Args:
        pdf_filename: Filename of the PDF (without path)
        extractor_class: Extractor class to use

    Example:
        >>> from custom_extractor import MyExtractor
        >>> register_extractor("special.pdf", MyExtractor)
    """
    EXTRACTOR_MAP[pdf_filename] = extractor_class


def list_registered_pdfs() -> Dict[str, str]:
    """
    Get a list of all registered PDF mappings.

    Returns:
        Dictionary mapping PDF filenames to extractor names

    Example:
        >>> mappings = list_registered_pdfs()
        >>> for pdf, extractor in mappings.items():
        ...     print(f"{pdf} -> {extractor}")
    """
    return {
        pdf: extractor.__name__
        for pdf, extractor in EXTRACTOR_MAP.items()
    }
