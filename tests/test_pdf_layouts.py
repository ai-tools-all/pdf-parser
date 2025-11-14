"""
Snapshot tests for PDF layout extraction.

These tests use syrupy for snapshot testing, which means they capture the
output of the extractors and compare against saved snapshots on subsequent runs.

Running tests:
    # Run all tests
    pytest tests/

    # Run only snapshot tests
    pytest tests/ -m snapshot

    # Update snapshots after intentional changes
    pytest tests/ --snapshot-update

    # Run tests for a specific extractor
    pytest tests/ -m "extractor(PDFColumnExtractor)"

    # Skip slow tests
    pytest tests/ -m "not slow"
"""

import pytest
from pathlib import Path

from pdf_layout_tester import (
    extract_with_implementation,
    extract_all_pages,
    PageRange,
    parse_pages_argument
)
from tests.extractor_config import get_extractor_for_pdf
from A003_colored_footer import PDFColumnExtractor


# ============================================================================
# Utility Tests (not snapshot tests)
# ============================================================================

class TestPageParsing:
    """Test page number parsing utilities."""

    def test_parse_single_page(self):
        """Test parsing a single page number."""
        result = parse_pages_argument(1)
        assert result == [1]

    def test_parse_page_list(self):
        """Test parsing a list of page numbers."""
        result = parse_pages_argument([1, 3, 5])
        assert result == [1, 3, 5]

    def test_parse_page_range(self):
        """Test parsing a PageRange object."""
        result = parse_pages_argument(PageRange(1, 5))
        assert result == [1, 2, 3, 4, 5]

    def test_parse_string_range(self):
        """Test parsing a string range like '1-5'."""
        result = parse_pages_argument("1-5")
        assert result == [1, 2, 3, 4, 5]

    def test_parse_string_single(self):
        """Test parsing a single page as string."""
        result = parse_pages_argument("3")
        assert result == [3]

    def test_parse_duplicates_removed(self):
        """Test that duplicate page numbers are removed."""
        result = parse_pages_argument([1, 3, 1, 5, 3])
        assert result == [1, 3, 5]

    def test_parse_invalid_page_number(self):
        """Test that invalid page numbers raise ValueError."""
        with pytest.raises(ValueError):
            parse_pages_argument(0)

        with pytest.raises(ValueError):
            parse_pages_argument(-1)

    def test_parse_invalid_range(self):
        """Test that invalid ranges raise ValueError."""
        with pytest.raises(ValueError):
            parse_pages_argument("5-1")  # End < start

        with pytest.raises(ValueError):
            parse_pages_argument("invalid")


# ============================================================================
# Snapshot Tests - Single Page Extraction
# ============================================================================

class TestSinglePageExtraction:
    """
    Test extraction of single pages from PDFs.

    These tests create snapshots of the extraction output. On first run,
    they create the snapshot files. On subsequent runs, they compare against
    the saved snapshots.
    """

    @pytest.mark.snapshot
    @pytest.mark.extractor("PDFColumnExtractor")
    def test_extract_first_page(self, test_pdf_path, snapshot):
        """Test extraction of the first page."""
        if test_pdf_path is None:
            pytest.skip("No test PDF available")

        extractor_class = get_extractor_for_pdf(test_pdf_path)
        result = extract_with_implementation(
            pdf_path=test_pdf_path,
            pages=1,
            extractor_class=extractor_class
        )

        # Compare normalized output against snapshot
        assert result.to_dict(normalize=True) == snapshot

    @pytest.mark.snapshot
    @pytest.mark.extractor("PDFColumnExtractor")
    def test_extract_second_page(self, test_pdf_path, snapshot):
        """Test extraction of the second page."""
        if test_pdf_path is None:
            pytest.skip("No test PDF available")

        extractor_class = get_extractor_for_pdf(test_pdf_path)

        try:
            result = extract_with_implementation(
                pdf_path=test_pdf_path,
                pages=2,
                extractor_class=extractor_class
            )
            assert result.to_dict(normalize=True) == snapshot
        except IndexError:
            pytest.skip("PDF has fewer than 2 pages")


# ============================================================================
# Snapshot Tests - Multiple Page Extraction
# ============================================================================

class TestMultiplePageExtraction:
    """Test extraction of multiple pages."""

    @pytest.mark.snapshot
    @pytest.mark.extractor("PDFColumnExtractor")
    def test_extract_page_range(self, test_pdf_path, snapshot):
        """Test extraction of a range of pages."""
        if test_pdf_path is None:
            pytest.skip("No test PDF available")

        extractor_class = get_extractor_for_pdf(test_pdf_path)

        try:
            result = extract_with_implementation(
                pdf_path=test_pdf_path,
                pages=PageRange(1, 3),
                extractor_class=extractor_class
            )
            assert result.to_dict(normalize=True) == snapshot
        except IndexError:
            pytest.skip("PDF has fewer than 3 pages")

    @pytest.mark.snapshot
    @pytest.mark.extractor("PDFColumnExtractor")
    def test_extract_specific_pages(self, test_pdf_path, snapshot):
        """Test extraction of specific non-consecutive pages."""
        if test_pdf_path is None:
            pytest.skip("No test PDF available")

        extractor_class = get_extractor_for_pdf(test_pdf_path)

        try:
            result = extract_with_implementation(
                pdf_path=test_pdf_path,
                pages=[1, 3],  # Non-consecutive pages
                extractor_class=extractor_class
            )
            assert result.to_dict(normalize=True) == snapshot
        except IndexError:
            pytest.skip("PDF has fewer than 3 pages")

    @pytest.mark.snapshot
    @pytest.mark.slow
    @pytest.mark.extractor("PDFColumnExtractor")
    def test_extract_all_pages(self, test_pdf_path, snapshot):
        """Test extraction of all pages (marked as slow)."""
        if test_pdf_path is None:
            pytest.skip("No test PDF available")

        extractor_class = get_extractor_for_pdf(test_pdf_path)

        result = extract_all_pages(
            pdf_path=test_pdf_path,
            extractor_class=extractor_class
        )

        assert result.to_dict(normalize=True) == snapshot


# ============================================================================
# Layout Structure Tests
# ============================================================================

class TestLayoutStructure:
    """
    Test the structure and content of extracted layouts.

    These tests verify that the extractors produce the expected structure
    without using snapshots.
    """

    def test_layout_has_required_fields(self, test_pdf_path):
        """Test that extracted layouts have all required fields."""
        if test_pdf_path is None:
            pytest.skip("No test PDF available")

        extractor_class = get_extractor_for_pdf(test_pdf_path)
        result = extract_with_implementation(
            pdf_path=test_pdf_path,
            pages=1,
            extractor_class=extractor_class
        )

        # Check that we got results
        assert len(result.pages) == 1
        layout = result.pages[0]

        # Check all required fields are present
        assert hasattr(layout, 'page_number')
        assert hasattr(layout, 'header')
        assert hasattr(layout, 'footer')
        assert hasattr(layout, 'left_column')
        assert hasattr(layout, 'right_column')
        assert hasattr(layout, 'page_width')
        assert hasattr(layout, 'page_height')
        assert hasattr(layout, 'column_separator_position')
        assert hasattr(layout, 'metadata')

        # Check types
        assert isinstance(layout.page_number, int)
        assert isinstance(layout.header, str)
        assert isinstance(layout.footer, str)
        assert isinstance(layout.left_column, str)
        assert isinstance(layout.right_column, str)
        assert isinstance(layout.page_width, float)
        assert isinstance(layout.page_height, float)
        assert isinstance(layout.metadata, dict)

    def test_page_numbers_are_sequential(self, test_pdf_path):
        """Test that page numbers in results are sequential and correct."""
        if test_pdf_path is None:
            pytest.skip("No test PDF available")

        extractor_class = get_extractor_for_pdf(test_pdf_path)

        try:
            result = extract_with_implementation(
                pdf_path=test_pdf_path,
                pages=PageRange(1, 3),
                extractor_class=extractor_class
            )

            page_numbers = [layout.page_number for layout in result.pages]
            assert page_numbers == [1, 2, 3]
        except IndexError:
            pytest.skip("PDF has fewer than 3 pages")

    def test_metadata_contains_blocks_count(self, test_pdf_path):
        """Test that metadata contains text block counts."""
        if test_pdf_path is None:
            pytest.skip("No test PDF available")

        extractor_class = get_extractor_for_pdf(test_pdf_path)
        result = extract_with_implementation(
            pdf_path=test_pdf_path,
            pages=1,
            extractor_class=extractor_class
        )

        layout = result.pages[0]
        metadata = layout.metadata

        # Check for expected metadata fields (specific to PDFColumnExtractor)
        if extractor_class.__name__ == "PDFColumnExtractor":
            assert 'total_text_blocks' in metadata
            assert 'header_blocks' in metadata
            assert 'footer_blocks' in metadata
            assert 'left_column_blocks' in metadata
            assert 'right_column_blocks' in metadata


# ============================================================================
# Example: Testing with Custom PDFs
# ============================================================================

# Uncomment and customize this example when you have specific test PDFs

# @pytest.mark.snapshot
# @pytest.mark.extractor("PDFColumnExtractor")
# def test_academic_paper_first_page(data_dir, snapshot):
#     """Test extraction from an academic paper."""
#     pdf_path = data_dir / "academic_paper.pdf"
#
#     if not pdf_path.exists():
#         pytest.skip("academic_paper.pdf not found in data_dir")
#
#     extractor_class = get_extractor_for_pdf(pdf_path)
#     result = extract_with_implementation(
#         pdf_path=pdf_path,
#         pages=1,
#         extractor_class=extractor_class
#     )
#
#     assert result.to_dict(normalize=True) == snapshot


# ============================================================================
# Example: Comparing Multiple Extractors
# ============================================================================

# Uncomment this example to compare different extractors on the same PDF

# from pdf_layout_tester import compare_extractors
# from A002_header_footer_2_col import SimpleExtractor
#
# @pytest.mark.snapshot
# def test_compare_extractors(test_pdf_path, snapshot):
#     """Compare outputs from different extractors."""
#     if test_pdf_path is None:
#         pytest.skip("No test PDF available")
#
#     results = compare_extractors(
#         pdf_path=test_pdf_path,
#         pages=1,
#         extractor_classes=[PDFColumnExtractor, SimpleExtractor]
#     )
#
#     # Convert to comparable format
#     comparison = {
#         name: result.to_dict(normalize=True)
#         for name, result in results.items()
#     }
#
#     assert comparison == snapshot
