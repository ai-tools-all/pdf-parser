"""
Pytest configuration for PDF layout snapshot testing.

This module configures pytest and syrupy for snapshot testing of PDF extractors.
"""

import pytest
from pathlib import Path


@pytest.fixture
def snapshot(snapshot):
    """
    Syrupy snapshot fixture with custom configuration.

    The snapshot fixture is provided by syrupy and automatically handles
    snapshot creation, comparison, and updates.
    """
    return snapshot


@pytest.fixture
def data_dir():
    """
    Fixture providing the path to test data directory.

    Returns:
        Path: Path to the data_dir directory where test PDFs are stored

    Usage:
        def test_something(data_dir):
            pdf_path = data_dir / "test_document.pdf"
    """
    return Path(__file__).parent.parent / "data_dir"


@pytest.fixture
def test_pdf_path(data_dir):
    """
    Fixture providing a default test PDF path.

    Returns:
        Path: Path to document.pdf if it exists, otherwise None

    Usage:
        def test_extraction(test_pdf_path):
            if test_pdf_path is None:
                pytest.skip("No test PDF available")
            # ... use test_pdf_path
    """
    pdf_path = data_dir / "document.pdf"
    return pdf_path if pdf_path.exists() else None


def pytest_configure(config):
    """
    Pytest configuration hook.

    Registers custom markers for organizing tests.
    """
    config.addinivalue_line(
        "markers",
        "snapshot: marks tests as snapshot tests (deselect with '-m \"not snapshot\"')"
    )
    config.addinivalue_line(
        "markers",
        "extractor(name): marks tests for a specific extractor implementation"
    )
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
