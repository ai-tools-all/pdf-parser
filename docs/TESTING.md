# PDF Layout Testing Guide

This guide explains how to test PDF layout extraction scripts using snapshot testing. The testing framework is designed to work with any extractor that implements the `PDFLayoutExtractor` protocol, allowing you to test modifications and improvements to extraction scripts with confidence.

## Table of Contents

1. [Overview](#overview)
2. [Setup](#setup)
3. [Understanding Snapshot Testing](#understanding-snapshot-testing)
4. [Running Tests](#running-tests)
5. [Writing New Tests](#writing-new-tests)
6. [Testing Script Modifications](#testing-script-modifications)
7. [Creating New Extractors](#creating-new-extractors)
8. [Configuration](#configuration)
9. [Troubleshooting](#troubleshooting)

## Overview

### What is Snapshot Testing?

Snapshot testing is a testing technique where you capture the output of your code and save it as a "snapshot". On subsequent test runs, the current output is compared against the saved snapshot. If they match, the test passes. If they differ, either you've introduced a bug or you've made an intentional change that needs a snapshot update.

### Why Use Snapshot Testing for PDFs?

PDF layout extraction produces complex, nested output (headers, footers, columns, metadata). Writing assertions for all this data manually would be tedious and brittle. Snapshot testing:

- ✅ Automatically captures the entire output structure
- ✅ Makes it easy to detect unintended changes
- ✅ Provides clear diffs when output changes
- ✅ Reduces test maintenance burden

### Architecture

The testing framework has three main components:

1. **Protocol Definition** (`pdf_extractor_protocol.py`)
   - Defines the `PDFLayoutExtractor` protocol
   - Defines the standard `PageLayout` output format
   - Ensures all extractors have a consistent interface

2. **Testing Framework** (`pdf_layout_tester.py`)
   - Provides utilities for running extractors
   - Handles page number parsing (single, ranges, lists)
   - Normalizes output for consistent snapshots

3. **Test Suite** (`tests/`)
   - Contains the actual test cases
   - Uses syrupy for snapshot management
   - Configured via `extractor_config.py`

## Setup

### Install Dependencies

```bash
# Install test dependencies
uv pip install -e ".[test]"

# Or using pip
pip install -e ".[test]"
```

This installs:
- `pytest` - Test runner
- `syrupy` - Snapshot testing library
- `pytest-xdist` - Parallel test execution

### Verify Installation

```bash
pytest --version
pytest --co tests/  # List all tests without running them
```

## Understanding Snapshot Testing

### How Snapshots Work

1. **First Run** - Creates snapshot files
   ```bash
   pytest tests/test_pdf_layouts.py::test_extract_first_page
   ```
   This creates a snapshot file in `tests/__snapshots__/test_pdf_layouts.ambr`

2. **Subsequent Runs** - Compares against snapshots
   ```bash
   pytest tests/test_pdf_layouts.py::test_extract_first_page
   ```
   If output matches the snapshot: ✅ Test passes
   If output differs: ❌ Test fails with a diff

3. **Updating Snapshots** - After intentional changes
   ```bash
   pytest tests/ --snapshot-update
   ```
   This updates all snapshot files with new output

### Snapshot File Format

Snapshots are stored in `tests/__snapshots__/*.ambr` files using syrupy's format:

```python
# serializer version: 1
# name: test_extract_first_page
  dict({
    'extractor': 'PDFColumnExtractor',
    'pages': list([
      dict({
        'footer': 'Page 1',
        'header': 'Document Title',
        'left_column': 'Left column text...',
        ...
      }),
    ]),
    ...
  })
```

## Running Tests

### Run All Tests

```bash
pytest tests/
```

### Run Specific Tests

```bash
# Run a specific test file
pytest tests/test_pdf_layouts.py

# Run a specific test class
pytest tests/test_pdf_layouts.py::TestSinglePageExtraction

# Run a specific test
pytest tests/test_pdf_layouts.py::TestSinglePageExtraction::test_extract_first_page
```

### Run Tests by Marker

```bash
# Run only snapshot tests
pytest tests/ -m snapshot

# Skip slow tests
pytest tests/ -m "not slow"

# Run tests for a specific extractor
pytest tests/ -m "extractor(PDFColumnExtractor)"
```

### Parallel Execution

```bash
# Run tests in parallel (faster for large test suites)
pytest tests/ -n auto
```

### Verbose Output

```bash
# Show detailed output
pytest tests/ -v

# Show print statements
pytest tests/ -s

# Show full diff on failures
pytest tests/ -vv
```

## Writing New Tests

### Basic Snapshot Test

```python
import pytest
from pdf_layout_tester import extract_with_implementation
from tests.extractor_config import get_extractor_for_pdf

@pytest.mark.snapshot
def test_my_pdf(snapshot, data_dir):
    """Test extraction from my_document.pdf"""
    pdf_path = data_dir / "my_document.pdf"

    if not pdf_path.exists():
        pytest.skip("PDF not found")

    extractor_class = get_extractor_for_pdf(pdf_path)
    result = extract_with_implementation(
        pdf_path=pdf_path,
        pages=1,
        extractor_class=extractor_class
    )

    assert result.to_dict(normalize=True) == snapshot
```

### Testing Multiple Pages

```python
from pdf_layout_tester import PageRange

@pytest.mark.snapshot
def test_page_range(test_pdf_path, snapshot):
    """Test extracting pages 1-5"""
    extractor_class = get_extractor_for_pdf(test_pdf_path)
    result = extract_with_implementation(
        pdf_path=test_pdf_path,
        pages=PageRange(1, 5),
        extractor_class=extractor_class
    )

    assert result.to_dict(normalize=True) == snapshot
```

### Testing Specific Pages

```python
@pytest.mark.snapshot
def test_specific_pages(test_pdf_path, snapshot):
    """Test extracting specific non-consecutive pages"""
    extractor_class = get_extractor_for_pdf(test_pdf_path)
    result = extract_with_implementation(
        pdf_path=test_pdf_path,
        pages=[1, 5, 10],  # Non-consecutive pages
        extractor_class=extractor_class
    )

    assert result.to_dict(normalize=True) == snapshot
```

### Structure Tests (No Snapshots)

Sometimes you want to test the structure without snapshot comparison:

```python
def test_layout_structure(test_pdf_path):
    """Test that layout has expected structure"""
    extractor_class = get_extractor_for_pdf(test_pdf_path)
    result = extract_with_implementation(
        pdf_path=test_pdf_path,
        pages=1,
        extractor_class=extractor_class
    )

    layout = result.pages[0]

    # Assert specific conditions
    assert layout.page_number == 1
    assert isinstance(layout.header, str)
    assert layout.page_width > 0
    assert layout.page_height > 0
    assert 'total_text_blocks' in layout.metadata
```

## Testing Script Modifications

This section explains the **workflow for testing changes** to PDF extraction scripts.

### Workflow Overview

When you modify an extraction script (e.g., improve footer detection in `A003_colored_footer.py`), follow this workflow:

1. **Before Making Changes** - Ensure tests pass
2. **Make Your Changes** - Modify the extractor
3. **Run Tests** - See what changed
4. **Review Differences** - Verify changes are correct
5. **Update Snapshots** - If changes are intentional
6. **Commit** - Save your work

### Step-by-Step Example

Let's say you want to improve colored footer detection in `A003_colored_footer.py`:

#### 1. Before Making Changes

```bash
# Ensure all tests pass with current implementation
pytest tests/ -m snapshot

# Output should show all tests passing
# ================= 8 passed in 2.31s =================
```

#### 2. Make Your Changes

Edit `A003_colored_footer.py` to improve the `detect_colored_backgrounds` method:

```python
def detect_colored_backgrounds(self, page) -> List[Tuple[float, float, float, float]]:
    """Detect rectangles with colored backgrounds that might indicate footers"""
    colored_regions = []

    try:
        drawings = page.get_drawings()
        for drawing in drawings:
            if "items" in drawing and "fill" in drawing:
                fill_color = drawing.get("fill")
                # NEW: Also detect light gray backgrounds (not just colored)
                if fill_color and fill_color != [1.0, 1.0, 1.0]:
                    if "rect" in drawing:
                        rect = drawing["rect"]
                        if len(rect) >= 4:
                            colored_regions.append(tuple(rect[:4]))
    except Exception as e:
        print(f"Warning: Could not detect colored backgrounds: {e}")

    return colored_regions
```

#### 3. Run Tests to See Changes

```bash
pytest tests/test_pdf_layouts.py::test_extract_first_page -v
```

The test will likely fail with output showing the differences:

```
FAILED tests/test_pdf_layouts.py::test_extract_first_page - AssertionError

================================ FAILURES =================================
___________________________ test_extract_first_page _______________________

Snapshot summary:
  1 snapshot failed.

------------------- Snapshot Diff -------------------
  dict({
    'extractor': 'PDFColumnExtractor',
    'pages': list([
      dict({
-       'footer': '',
+       'footer': 'Document Footer Text',
        'header': 'Document Title',
        ...
        'metadata': dict({
-         'footer_blocks': 0,
+         'footer_blocks': 1,
        }),
      }),
    ]),
  })
```

#### 4. Review the Differences

Examine the diff carefully:

- ✅ **Expected change**: Footer is now detected (was empty, now has text)
- ✅ **Expected change**: `footer_blocks` increased from 0 to 1
- ❌ **Unexpected change**: If you see other unexpected differences, investigate!

#### 5. Verify with Manual Inspection

You can also manually inspect the output:

```python
# Create a test script: inspect_output.py
from pdf_layout_tester import extract_with_implementation
from A003_colored_footer import PDFColumnExtractor

result = extract_with_implementation(
    pdf_path="data_dir/document.pdf",
    pages=1,
    extractor_class=PDFColumnExtractor
)

print(result.to_json())
```

```bash
python inspect_output.py | less
```

#### 6. Update Snapshots if Correct

If the changes look correct:

```bash
# Update snapshots for all tests
pytest tests/ --snapshot-update

# Or update just one test
pytest tests/test_pdf_layouts.py::test_extract_first_page --snapshot-update
```

#### 7. Verify Tests Pass

```bash
pytest tests/ -m snapshot

# Should now pass:
# ================= 8 passed in 2.31s =================
```

#### 8. Commit Your Changes

```bash
git add A003_colored_footer.py tests/__snapshots__/
git commit -m "Improve colored footer detection to include light gray backgrounds"
```

### Testing Against Multiple PDFs

To ensure your changes work across different PDFs:

```python
# Add tests for different PDF types
@pytest.mark.snapshot
@pytest.mark.parametrize("pdf_name", [
    "academic_paper.pdf",
    "business_report.pdf",
    "simple_document.pdf"
])
def test_multiple_pdfs(pdf_name, data_dir, snapshot):
    """Test extractor on various PDF types"""
    pdf_path = data_dir / pdf_name
    if not pdf_path.exists():
        pytest.skip(f"{pdf_name} not found")

    extractor_class = get_extractor_for_pdf(pdf_path)
    result = extract_with_implementation(
        pdf_path=pdf_path,
        pages=1,
        extractor_class=extractor_class
    )

    assert result.to_dict(normalize=True) == snapshot
```

## Creating New Extractors

### Step 1: Implement the Protocol

Create a new extractor that implements `PDFLayoutExtractor`:

```python
# my_custom_extractor.py
import fitz
from pdf_extractor_protocol import PageLayout, PDFLayoutExtractor

class MyCustomExtractor:
    """
    Custom PDF extractor with special handling for XYZ layout.

    Implements the PDFLayoutExtractor protocol.
    """

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)

    def extract_page_layout(self, page_num: int) -> PageLayout:
        """Extract layout from a single page (0-indexed)."""
        page = self.doc[page_num]

        # Your custom extraction logic here
        header = self._extract_header(page)
        footer = self._extract_footer(page)
        # ... etc

        return PageLayout(
            page_number=page_num + 1,  # Convert to 1-indexed
            header=header,
            footer=footer,
            left_column=left_text,
            right_column=right_text,
            page_width=page.rect.width,
            page_height=page.rect.height,
            column_separator_position=separator_x,
            metadata=metadata_dict
        )

    def extract_all_pages(self) -> List[PageLayout]:
        """Extract all pages."""
        return [
            self.extract_page_layout(i)
            for i in range(len(self.doc))
        ]

    def close(self):
        """Clean up resources."""
        self.doc.close()

    # Your custom methods
    def _extract_header(self, page):
        # ... implementation
        pass
```

### Step 2: Validate Protocol Compliance

```python
from pdf_extractor_protocol import validate_extractor
from my_custom_extractor import MyCustomExtractor

# This will raise an error if the protocol is not correctly implemented
validate_extractor(MyCustomExtractor)
```

### Step 3: Register in Configuration

Add your extractor to `tests/extractor_config.py`:

```python
from my_custom_extractor import MyCustomExtractor

EXTRACTOR_MAP = {
    "document.pdf": PDFColumnExtractor,
    "special_layout.pdf": MyCustomExtractor,  # Use your new extractor
}
```

### Step 4: Create Tests

```python
@pytest.mark.snapshot
@pytest.mark.extractor("MyCustomExtractor")
def test_custom_extractor(snapshot, data_dir):
    """Test the custom extractor."""
    pdf_path = data_dir / "special_layout.pdf"

    result = extract_with_implementation(
        pdf_path=pdf_path,
        pages=1,
        extractor_class=MyCustomExtractor
    )

    assert result.to_dict(normalize=True) == snapshot
```

## Configuration

### Configuring PDF-to-Extractor Mapping

Edit `tests/extractor_config.py`:

```python
EXTRACTOR_MAP = {
    # Map specific PDFs to their best extractor
    "academic_paper.pdf": PDFColumnExtractor,
    "simple_doc.pdf": SimpleExtractor,
    "complex_layout.pdf": CustomExtractor,
}

# Default for unmapped PDFs
DEFAULT_EXTRACTOR = PDFColumnExtractor
```

### Pytest Configuration

The `pyproject.toml` file contains pytest settings:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = ["-v", "--strict-markers"]
markers = [
    "snapshot: snapshot tests",
    "slow: marks tests as slow",
    "extractor: marks tests for specific extractor",
]
```

## Troubleshooting

### Tests Fail with "PDF file not found"

**Problem**: Test tries to access a PDF that doesn't exist.

**Solution**:
- Add the PDF to `data_dir/` directory
- Or skip the test if PDF is optional:
  ```python
  if not pdf_path.exists():
      pytest.skip("PDF not available")
  ```

### Snapshots Keep Failing Due to Floating Point Differences

**Problem**: Small floating point precision differences cause snapshot failures.

**Solution**: Ensure you're using `normalize=True`:
```python
assert result.to_dict(normalize=True) == snapshot
```

The normalizer rounds floats to 2 decimal places.

### How to Delete Old Snapshots

**Problem**: You've renamed or removed tests, but old snapshots remain.

**Solution**:
```bash
# Syrupy will warn about unused snapshots
pytest tests/ --snapshot-update

# Manually delete unused snapshots from tests/__snapshots__/
```

### Snapshots Look Different on Different Machines

**Problem**: PDF rendering or text extraction varies by platform.

**Solution**:
- Use Docker for consistent environments
- Pin PyMuPDF version in dependencies
- Normalize output more aggressively
- Consider platform-specific snapshot directories

### Test Discovery Issues

**Problem**: pytest doesn't find your tests.

**Solution**:
- Ensure test files are named `test_*.py`
- Ensure test functions are named `test_*`
- Check that `tests/` directory has `__init__.py` (optional but recommended)

### Import Errors

**Problem**: `ModuleNotFoundError` when running tests.

**Solution**:
```bash
# Install the package in editable mode
pip install -e .

# Or add parent directory to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest tests/
```

## Best Practices

### 1. Test Incrementally

Don't write all tests at once. Start with one test, make sure it works, then expand.

### 2. Use Descriptive Test Names

```python
# Good
def test_extract_first_page_with_colored_footer():
    ...

# Less clear
def test_page1():
    ...
```

### 3. Keep Snapshots in Version Control

Always commit snapshot files (`tests/__snapshots__/`). They are part of your test suite.

### 4. Review Snapshot Diffs Carefully

When updating snapshots, always review the diff to ensure changes are intentional.

### 5. Test Edge Cases

```python
# Empty pages
def test_extract_empty_page()

# Single-column layouts
def test_extract_single_column()

# Pages without headers/footers
def test_extract_no_header_footer()
```

### 6. Use Parametrized Tests for Multiple Scenarios

```python
@pytest.mark.parametrize("page_num,expected_has_footer", [
    (1, True),
    (2, False),
    (3, True),
])
def test_footer_detection(page_num, expected_has_footer, test_pdf_path):
    result = extract_with_implementation(
        pdf_path=test_pdf_path,
        pages=page_num,
        extractor_class=PDFColumnExtractor
    )
    layout = result.pages[0]
    assert (len(layout.footer) > 0) == expected_has_footer
```

## Additional Resources

- [Syrupy Documentation](https://github.com/syrupy-project/syrupy)
- [Pytest Documentation](https://docs.pytest.org/)
- [PyMuPDF Documentation](https://pymupdf.readthedocs.io/)

## Getting Help

If you encounter issues:

1. Check this documentation
2. Review example tests in `tests/test_pdf_layouts.py`
3. Run tests with `-vv` for detailed output
4. Check the snapshot diff output
5. Validate your extractor with `validate_extractor()`
