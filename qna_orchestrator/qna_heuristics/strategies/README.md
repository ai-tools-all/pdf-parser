# Parser Strategies

This directory contains the strategy interfaces and implementations for the composable parser architecture.

## Overview

The composable parser separates PDF parsing into three pluggable strategies:

```
┌─────────────────────────────────────────────────────────┐
│              ComposableParser                            │
└───────────┬─────────────┬──────────────┬────────────────┘
            │             │              │
            ▼             ▼              ▼
    ┌──────────┐  ┌──────────┐  ┌─────────────┐
    │  Text    │  │  Layout  │  │  Heuristic  │
    │Extraction│  │Detection │  │  Analysis   │
    │ Strategy │  │ Strategy │  │  Strategy   │
    └──────────┘  └──────────┘  └─────────────┘
```

## Strategy Interfaces

### 1. TextExtractionStrategy (`extraction.py`)

**Purpose:** Extract raw text blocks from PDF files

**Key Methods:**
- `extract_blocks(pdf_path, page_num)` - Extract text blocks from a page
- `get_page_dimensions(pdf_path, page_num)` - Get page width/height
- `get_page_count(pdf_path)` - Get total number of pages

**Data Types:**
- `RawTextBlock` - Pre-processed text block with position and styling

**When to implement:**
- Adding support for different PDF libraries (pdfplumber, camelot, etc.)
- Implementing vision-based extraction (LayoutLM, Donut, etc.)
- Custom extraction logic for specific document types

**Example:**
```python
from qna_orchestrator.qna_heuristics.strategies import TextExtractionStrategy, RawTextBlock

class MyCustomExtractor:
    def extract_blocks(self, pdf_path: str, page_num: int) -> List[RawTextBlock]:
        # Your extraction logic here
        blocks = []
        # ... extract text ...
        return blocks
```

---

### 2. LayoutDetectionStrategy (`layout.py`)

**Purpose:** Detect document layout and classify blocks into regions

**Key Methods:**
- `detect_layout(page, blocks)` - Analyze layout structure
- `classify_blocks(page, blocks, layout_info)` - Assign blocks to regions

**Data Types:**
- `LayoutInfo` - Layout metadata (columns, regions, boundaries)

**When to implement:**
- Supporting different column layouts (1-col, 2-col, 3-col, etc.)
- Complex layout patterns (mixed columns, tables, sidebars)
- ML-based layout detection

**Example:**
```python
from qna_orchestrator.qna_heuristics.strategies import LayoutDetectionStrategy, LayoutInfo

class SingleColumnLayout:
    def detect_layout(self, page, blocks):
        return LayoutInfo(
            column_count=1,
            column_separators=[],
            detected_layout_type="single_column"
        )
    
    def classify_blocks(self, page, blocks, layout_info):
        # All blocks go to left_column_blocks
        for block in blocks:
            # ... classification logic ...
            pass
```

---

### 3. HeuristicAnalysisStrategy (`analysis.py`)

**Purpose:** Apply heuristics to analyze content semantically

**Key Methods:**
- `analyze_blocks(blocks, page, config)` - Apply heuristics to blocks
- `get_heuristics()` - Return list of heuristic functions

**When to implement:**
- Custom heuristic combinations for specific document types
- Different analysis modes (aggressive, conservative, etc.)
- Domain-specific content detection

**Example:**
```python
from qna_orchestrator.qna_heuristics.strategies import HeuristicAnalysisStrategy

class CustomHeuristicAnalyzer:
    def __init__(self, heuristic_functions):
        self.heuristics = heuristic_functions
    
    def analyze_blocks(self, blocks, page, config):
        # Apply each heuristic
        for heuristic in self.heuristics:
            # ... analysis logic ...
            pass
    
    def get_heuristics(self):
        return self.heuristics
```

---

## Using ComposableParser

### Basic Usage

```python
from qna_orchestrator.qna_heuristics.composable_parser import ComposableParser
from qna_orchestrator.qna_heuristics.strategies.implementations import (
    PyMuPDFExtractor,
    TwoColumnLayoutDetector,
    DefaultHeuristicAnalyzer
)

# Create parser with strategies
parser = ComposableParser(
    extraction_strategy=PyMuPDFExtractor(config),
    layout_strategy=TwoColumnLayoutDetector(config),
    analysis_strategy=DefaultHeuristicAnalyzer(config),
    config=config
)

# Parse document
document = parser.parse("exam.pdf")
```

### Custom Strategy Combination

```python
# Mix and match strategies
parser = ComposableParser(
    extraction_strategy=PDFPlumberExtractor(config),  # Different extractor
    layout_strategy=TwoColumnLayoutDetector(config),   # Same layout
    analysis_strategy=AggressiveHeuristicAnalyzer(config),  # Different analysis
    config=config
)
```

---

## Implementation Status

| Strategy Type | Interface | Default Implementation | Alternative Implementations |
|--------------|-----------|------------------------|----------------------------|
| Text Extraction | ✅ Done | 🚧 Pending | 📝 Planned |
| Layout Detection | ✅ Done | 🚧 Pending | 📝 Planned |
| Heuristic Analysis | ✅ Done | 🚧 Pending | 📝 Planned |

**Legend:**
- ✅ Done - Complete and tested
- 🚧 Pending - In development
- 📝 Planned - Future work

---

## Adding a New Strategy

### Step 1: Implement the Protocol

Create a new class that implements one of the strategy protocols:

```python
# In implementations/my_strategy.py
from qna_orchestrator.qna_heuristics.strategies import TextExtractionStrategy

class MyExtractor:
    def __init__(self, config):
        self.config = config
    
    def extract_blocks(self, pdf_path: str, page_num: int):
        # Implementation
        pass
    
    def get_page_dimensions(self, pdf_path: str, page_num: int):
        # Implementation
        pass
    
    def get_page_count(self, pdf_path: str):
        # Implementation
        pass
```

### Step 2: Test Your Implementation

```python
# Test with ComposableParser
from qna_orchestrator.qna_heuristics.composable_parser import ComposableParser

parser = ComposableParser(
    extraction_strategy=MyExtractor(config),
    layout_strategy=existing_layout,
    analysis_strategy=existing_analysis,
    config=config
)

doc = parser.parse("test.pdf")
```

### Step 3: Register in Implementations

Add your implementation to `implementations/__init__.py`:

```python
from .my_strategy import MyExtractor

__all__ = [
    'MyExtractor',
    # ... other implementations
]
```

---

## Design Principles

1. **Single Responsibility**: Each strategy handles one concern
2. **Open/Closed**: Extend with new strategies without modifying existing code
3. **Dependency Inversion**: Depend on protocols, not concrete implementations
4. **Composability**: Mix and match strategies freely
5. **Testability**: Each strategy can be tested independently

---

## Next Steps

See [docs/2025-11-24_composable_parser_architecture.md](../../../docs/2025-11-24_composable_parser_architecture.md) for the full implementation plan.

**Upcoming:**
1. Implement default strategies (PyMuPDF, TwoColumn, DefaultAnalyzer)
2. Create ParserFactory for common presets
3. Add alternative implementations (pdfplumber, single-column, etc.)
4. Integrate with Orchestrator
5. Write comprehensive tests

---

## Questions?

For implementation details, see the architecture document.
For usage examples, see `docs/examples/` (coming soon).
