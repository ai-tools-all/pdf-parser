"""
PDF Layout Testing Framework

This module provides utilities for snapshot testing PDF layout extractors.
It works with any extractor implementing the PDFLayoutExtractor protocol,
allowing you to test different extraction strategies uniformly.

Example usage:
    from pdf_layout_tester import extract_with_implementation, PageRange
    from A003_colored_footer import PDFColumnExtractor

    # Test a single page
    result = extract_with_implementation(
        pdf_path="document.pdf",
        pages=1,
        extractor_class=PDFColumnExtractor
    )

    # Test a range of pages
    result = extract_with_implementation(
        pdf_path="document.pdf",
        pages=PageRange(1, 5),
        extractor_class=PDFColumnExtractor
    )

    # Test specific pages
    result = extract_with_implementation(
        pdf_path="document.pdf",
        pages=[1, 3, 5],
        extractor_class=PDFColumnExtractor
    )
"""

from typing import List, Dict, Union, Type, Optional
from dataclasses import dataclass
import json
from pathlib import Path

from pdf_extractor_protocol import (
    PageLayout,
    PDFLayoutExtractor,
    normalize_layout_for_snapshot,
    validate_extractor
)


@dataclass
class PageRange:
    """
    Represents a range of pages (inclusive).

    Args:
        start: First page number (1-indexed)
        end: Last page number (1-indexed, inclusive)
    """
    start: int
    end: int

    def to_list(self) -> List[int]:
        """Convert range to list of page numbers."""
        return list(range(self.start, self.end + 1))

    def __post_init__(self):
        if self.start < 1:
            raise ValueError("Page numbers must be >= 1")
        if self.end < self.start:
            raise ValueError("End page must be >= start page")


@dataclass
class ExtractionResult:
    """
    Result of a PDF layout extraction operation.

    Attributes:
        pdf_path: Path to the PDF that was processed
        extractor_name: Name of the extractor class used
        pages: List of PageLayout objects
        metadata: Additional information about the extraction
    """
    pdf_path: str
    extractor_name: str
    pages: List[PageLayout]
    metadata: Dict

    def to_dict(self, normalize: bool = True) -> Dict:
        """
        Convert result to dictionary.

        Args:
            normalize: If True, normalize layouts for snapshot testing

        Returns:
            Dictionary representation of the result
        """
        if normalize:
            pages_data = [normalize_layout_for_snapshot(page) for page in self.pages]
        else:
            pages_data = [page.to_dict() for page in self.pages]

        return {
            'pdf_path': self.pdf_path,
            'extractor': self.extractor_name,
            'total_pages': len(self.pages),
            'pages': pages_data,
            'metadata': self.metadata
        }

    def to_json(self, normalize: bool = True, **kwargs) -> str:
        """
        Convert result to JSON string.

        Args:
            normalize: If True, normalize layouts for snapshot testing
            **kwargs: Additional arguments passed to json.dumps

        Returns:
            JSON string representation
        """
        defaults = {'indent': 2, 'ensure_ascii': False}
        defaults.update(kwargs)
        return json.dumps(self.to_dict(normalize=normalize), **defaults)

    def save_to_file(self, output_path: Union[str, Path], normalize: bool = True):
        """
        Save result to a JSON file.

        Args:
            output_path: Path where the JSON file should be saved
            normalize: If True, normalize layouts for snapshot testing
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(self.to_json(normalize=normalize))


def parse_pages_argument(
    pages: Union[int, List[int], PageRange, str]
) -> List[int]:
    """
    Parse various page specifications into a list of 1-indexed page numbers.

    Args:
        pages: Page specification in various formats:
            - int: Single page number (e.g., 1)
            - List[int]: Multiple specific pages (e.g., [1, 3, 5])
            - PageRange: Range object (e.g., PageRange(1, 5))
            - str: String range (e.g., "1-5")

    Returns:
        List of 1-indexed page numbers

    Raises:
        ValueError: If the page specification is invalid
    """
    if isinstance(pages, int):
        if pages < 1:
            raise ValueError(f"Page number must be >= 1, got {pages}")
        return [pages]

    elif isinstance(pages, list):
        if not all(isinstance(p, int) and p >= 1 for p in pages):
            raise ValueError("All page numbers must be integers >= 1")
        return sorted(set(pages))  # Remove duplicates and sort

    elif isinstance(pages, PageRange):
        return pages.to_list()

    elif isinstance(pages, str):
        # Parse string range like "1-5"
        if '-' in pages:
            try:
                start, end = pages.split('-')
                start, end = int(start.strip()), int(end.strip())
                return PageRange(start, end).to_list()
            except (ValueError, AttributeError) as e:
                raise ValueError(f"Invalid page range string: {pages}") from e
        else:
            # Single page as string
            try:
                page_num = int(pages.strip())
                return [page_num]
            except ValueError as e:
                raise ValueError(f"Invalid page number string: {pages}") from e

    else:
        raise TypeError(
            f"Unsupported pages type: {type(pages)}. "
            f"Expected int, List[int], PageRange, or str"
        )


def extract_with_implementation(
    pdf_path: Union[str, Path],
    pages: Union[int, List[int], PageRange, str],
    extractor_class: Type[PDFLayoutExtractor],
    validate: bool = False
) -> ExtractionResult:
    """
    Extract PDF layout using a specific extractor implementation.

    This is the main function for testing PDF extractors. It works with any
    extractor that implements the PDFLayoutExtractor protocol.

    Args:
        pdf_path: Path to the PDF file
        pages: Page specification (see parse_pages_argument for formats)
        extractor_class: Class implementing PDFLayoutExtractor protocol
        validate: If True, validate the extractor implements the protocol

    Returns:
        ExtractionResult containing the extracted layouts

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        AttributeError: If extractor doesn't implement required methods
        ValueError: If page specification is invalid

    Example:
        >>> from A003_colored_footer import PDFColumnExtractor
        >>> result = extract_with_implementation(
        ...     "document.pdf",
        ...     pages=[1, 2],
        ...     extractor_class=PDFColumnExtractor
        ... )
        >>> print(result.to_json())
    """
    pdf_path = Path(pdf_path)

    # Validate inputs
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    if validate:
        validate_extractor(extractor_class)

    # Parse page numbers
    page_numbers = parse_pages_argument(pages)

    # Initialize extractor
    extractor = extractor_class(str(pdf_path))

    try:
        # Extract layouts for specified pages
        layouts = []
        for page_num in page_numbers:
            # Convert to 0-indexed for extractor
            layout = extractor.extract_page_layout(page_num - 1)
            layouts.append(layout)

        # Gather metadata
        metadata = {
            'requested_pages': page_numbers,
            'extracted_pages': len(layouts),
            'validation_performed': validate
        }

        return ExtractionResult(
            pdf_path=str(pdf_path),
            extractor_name=extractor_class.__name__,
            pages=layouts,
            metadata=metadata
        )

    finally:
        # Always clean up resources
        extractor.close()


def extract_all_pages(
    pdf_path: Union[str, Path],
    extractor_class: Type[PDFLayoutExtractor],
    validate: bool = False
) -> ExtractionResult:
    """
    Extract all pages from a PDF using a specific extractor.

    Args:
        pdf_path: Path to the PDF file
        extractor_class: Class implementing PDFLayoutExtractor protocol
        validate: If True, validate the extractor implements the protocol

    Returns:
        ExtractionResult containing all extracted layouts

    Example:
        >>> from A003_colored_footer import PDFColumnExtractor
        >>> result = extract_all_pages(
        ...     "document.pdf",
        ...     extractor_class=PDFColumnExtractor
        ... )
    """
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    if validate:
        validate_extractor(extractor_class)

    extractor = extractor_class(str(pdf_path))

    try:
        layouts = extractor.extract_all_pages()

        metadata = {
            'extraction_mode': 'all_pages',
            'extracted_pages': len(layouts),
            'validation_performed': validate
        }

        return ExtractionResult(
            pdf_path=str(pdf_path),
            extractor_name=extractor_class.__name__,
            pages=layouts,
            metadata=metadata
        )

    finally:
        extractor.close()


def compare_extractors(
    pdf_path: Union[str, Path],
    pages: Union[int, List[int], PageRange, str],
    extractor_classes: List[Type[PDFLayoutExtractor]]
) -> Dict[str, ExtractionResult]:
    """
    Compare multiple extractors on the same PDF pages.

    Useful for evaluating different extraction strategies or validating
    improvements to an extractor.

    Args:
        pdf_path: Path to the PDF file
        pages: Page specification
        extractor_classes: List of extractor classes to compare

    Returns:
        Dictionary mapping extractor names to their results

    Example:
        >>> from A002_header_footer_2_col import SimpleExtractor
        >>> from A003_colored_footer import PDFColumnExtractor
        >>> results = compare_extractors(
        ...     "document.pdf",
        ...     pages=1,
        ...     extractor_classes=[SimpleExtractor, PDFColumnExtractor]
        ... )
        >>> for name, result in results.items():
        ...     print(f"{name}: {len(result.pages)} pages")
    """
    results = {}

    for extractor_class in extractor_classes:
        result = extract_with_implementation(
            pdf_path=pdf_path,
            pages=pages,
            extractor_class=extractor_class
        )
        results[extractor_class.__name__] = result

    return results


# Convenience function for command-line usage
def main():
    """
    Command-line interface for quick testing.

    Run from command line:
        python pdf_layout_tester.py <pdf_path> <pages> [output_json]
    """
    import sys
    from A003_colored_footer import PDFColumnExtractor

    if len(sys.argv) < 3:
        print("Usage: python pdf_layout_tester.py <pdf_path> <pages> [output_json]")
        print("\nExamples:")
        print("  python pdf_layout_tester.py document.pdf 1")
        print("  python pdf_layout_tester.py document.pdf 1-5")
        print("  python pdf_layout_tester.py document.pdf 1,3,5 output.json")
        sys.exit(1)

    pdf_path = sys.argv[1]
    pages_arg = sys.argv[2]
    output_path = sys.argv[3] if len(sys.argv) > 3 else None

    # Parse pages argument
    if ',' in pages_arg:
        pages = [int(p.strip()) for p in pages_arg.split(',')]
    else:
        pages = pages_arg  # Will be parsed by parse_pages_argument

    # Extract
    print(f"Extracting from {pdf_path}, pages: {pages_arg}")
    result = extract_with_implementation(
        pdf_path=pdf_path,
        pages=pages,
        extractor_class=PDFColumnExtractor
    )

    # Output
    if output_path:
        result.save_to_file(output_path)
        print(f"Saved to {output_path}")
    else:
        print(result.to_json())


if __name__ == "__main__":
    main()
