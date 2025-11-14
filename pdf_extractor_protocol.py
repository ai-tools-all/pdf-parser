"""
Protocol definition for PDF layout extractors.

This module defines the interface that all PDF layout extractors must implement,
ensuring consistency across different extraction strategies and enabling
protocol-based testing.
"""

from typing import Protocol, List, Tuple, Dict, Optional, Union
from dataclasses import dataclass, asdict
import json


@dataclass
class PageLayout:
    """
    Standard output format for PDF page layout extraction.

    All extractors must return this dataclass (or a compatible structure)
    to ensure consistent testing and comparison.

    Attributes:
        page_number: 1-indexed page number
        header: Extracted header text
        footer: Extracted footer text
        left_column: Left column text content
        right_column: Right column text content
        page_width: Width of the page in points
        page_height: Height of the page in points
        column_separator_position: X-coordinate of column separator (if detected)
        metadata: Additional extractor-specific information
    """
    page_number: int
    header: str
    footer: str
    left_column: str
    right_column: str
    page_width: float
    page_height: float
    column_separator_position: Optional[float]
    metadata: Dict

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return asdict(self)

    def to_json(self, **kwargs) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), **kwargs)


class PDFLayoutExtractor(Protocol):
    """
    Protocol for PDF layout extractors.

    Any class implementing this protocol can be used with the testing framework.
    This ensures that different extraction strategies can be swapped and tested
    uniformly.

    Example:
        class MyExtractor:
            def __init__(self, pdf_path: str):
                self.pdf_path = pdf_path
                # ... initialization

            def extract_page_layout(self, page_num: int) -> PageLayout:
                # ... implementation
                return PageLayout(...)

            def extract_all_pages(self) -> List[PageLayout]:
                # ... implementation
                return [...]

            def close(self):
                # ... cleanup
                pass
    """

    pdf_path: str

    def __init__(self, pdf_path: str) -> None:
        """
        Initialize the extractor with a PDF file path.

        Args:
            pdf_path: Path to the PDF file to process
        """
        ...

    def extract_page_layout(self, page_num: int) -> PageLayout:
        """
        Extract layout information from a single page.

        Args:
            page_num: 0-indexed page number

        Returns:
            PageLayout object with extracted information
        """
        ...

    def extract_all_pages(self) -> List[PageLayout]:
        """
        Extract layout information from all pages in the PDF.

        Returns:
            List of PageLayout objects, one per page
        """
        ...

    def close(self) -> None:
        """
        Clean up resources (close PDF file handles, etc.).
        """
        ...


def validate_extractor(extractor_class: type) -> bool:
    """
    Validate that a class implements the PDFLayoutExtractor protocol.

    This function checks if the class has all required methods and attributes.
    Useful for testing and debugging new extractors.

    Args:
        extractor_class: The class to validate

    Returns:
        True if the class implements the protocol correctly

    Raises:
        AttributeError: If required methods/attributes are missing
        TypeError: If methods have incorrect signatures
    """
    required_methods = {
        '__init__': ['pdf_path'],
        'extract_page_layout': ['page_num'],
        'extract_all_pages': [],
        'close': []
    }

    for method_name, params in required_methods.items():
        if not hasattr(extractor_class, method_name):
            raise AttributeError(
                f"Extractor class {extractor_class.__name__} is missing "
                f"required method: {method_name}"
            )

        method = getattr(extractor_class, method_name)
        if not callable(method):
            raise TypeError(
                f"{method_name} in {extractor_class.__name__} is not callable"
            )

    return True


def normalize_layout_for_snapshot(layout: PageLayout) -> Dict:
    """
    Normalize a PageLayout for snapshot testing.

    This function prepares the layout data for consistent snapshot comparison
    by sorting dictionaries, rounding floats, and formatting strings.

    Args:
        layout: PageLayout object to normalize

    Returns:
        Normalized dictionary ready for snapshot comparison
    """
    data = layout.to_dict()

    # Round floating point numbers to avoid precision differences
    if data['page_width']:
        data['page_width'] = round(data['page_width'], 2)
    if data['page_height']:
        data['page_height'] = round(data['page_height'], 2)
    if data['column_separator_position']:
        data['column_separator_position'] = round(data['column_separator_position'], 2)

    # Sort metadata keys for consistent ordering
    if data['metadata']:
        data['metadata'] = dict(sorted(data['metadata'].items()))

    # Normalize whitespace in text fields
    for text_field in ['header', 'footer', 'left_column', 'right_column']:
        if data[text_field]:
            # Normalize line endings and excessive whitespace
            data[text_field] = '\n'.join(
                line.strip() for line in data[text_field].split('\n')
            ).strip()

    return data
