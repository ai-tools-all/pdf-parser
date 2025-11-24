# Custom Parser Strategies - Usage Examples

This guide shows how to create and integrate custom strategies with the composable parser architecture.

---

## Table of Contents

1. [Using Default Parser](#using-default-parser)
2. [Creating Custom Extraction Strategy](#creating-custom-extraction-strategy)
3. [Creating Custom Layout Strategy](#creating-custom-layout-strategy)
4. [Creating Custom Heuristic Strategy](#creating-custom-heuristic-strategy)
5. [Combining Custom Strategies](#combining-custom-strategies)
6. [Real-World Examples](#real-world-examples)

---

## Using Default Parser

The simplest way - just use the orchestrator with default settings:

```python
from qna_orchestrator.qna_heuristics.config import get_config
from qna_orchestrator.qna_heuristics.orchestrator import Orchestrator

# Create orchestrator with default parser
orchestrator = Orchestrator()

# Extract MCQs
mcqs = orchestrator.run("exam.pdf")
```

---

## Creating Custom Extraction Strategy

Create a custom text extractor (e.g., using pdfplumber instead of PyMuPDF):

```python
from typing import List, Tuple
import pdfplumber
from qna_orchestrator.qna_heuristics.strategies.extraction import RawTextBlock

class PDFPlumberExtractor:
    """Custom extractor using pdfplumber for better table handling."""
    
    def __init__(self, config):
        self.config = config
    
    def extract_blocks(self, pdf_path: str, page_num: int) -> List[RawTextBlock]:
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[page_num]
            
            # Extract words with positions
            words = page.extract_words()
            
            blocks = []
            for word in words:
                block = RawTextBlock(
                    text=word['text'],
                    bbox=(word['x0'], word['top'], word['x1'], word['bottom']),
                    font_size=word.get('height', 12),
                    font_name=word.get('fontname', 'Unknown'),
                    page_number=page_num + 1
                )
                blocks.append(block)
            
            # Sort by reading order
            blocks.sort(key=lambda b: (b.y0, b.x0))
            return blocks
    
    def get_page_dimensions(self, pdf_path: str, page_num: int) -> Tuple[float, float]:
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[page_num]
            return (page.width, page.height)
    
    def get_page_count(self, pdf_path: str) -> int:
        with pdfplumber.open(pdf_path) as pdf:
            return len(pdf.pages)

# Use it
from qna_orchestrator.qna_heuristics.config import get_config
from qna_orchestrator.qna_heuristics.parser_factory import ParserFactory
from qna_orchestrator.qna_heuristics.orchestrator import Orchestrator

config = get_config()

parser = ParserFactory.create_custom(
    extraction=PDFPlumberExtractor(config),
    layout=TwoColumnLayoutDetector(config),  # Use default layout
    analysis=DefaultHeuristicAnalyzer(config),  # Use default analysis
    config=config
)

orchestrator = Orchestrator(parser=parser)
mcqs = orchestrator.run("exam.pdf")
```

---

## Creating Custom Layout Strategy

Create a single-column layout detector:

```python
from qna_orchestrator.qna_heuristics.strategies.layout import LayoutInfo
from qna_orchestrator.qna_heuristics.data_models import TextBlock

class SingleColumnLayoutDetector:
    """Simple single-column layout - no column splitting."""
    
    def __init__(self, config):
        self.config = config
        parser_config = config.get("PARSER", {})
        self.header_percent = parser_config.get("HEADER_REGION_PERCENT", 0.1)
        self.footer_percent = parser_config.get("FOOTER_REGION_PERCENT", 0.9)
    
    def detect_layout(self, page, blocks):
        """Single column = no separator needed."""
        return LayoutInfo(
            column_count=1,
            column_separators=[],  # No separator
            header_boundary=self.header_percent,
            footer_boundary=self.footer_percent,
            detected_layout_type="single_column",
            confidence=1.0
        )
    
    def classify_blocks(self, page, blocks, layout_info):
        """All content blocks go to left_column_blocks."""
        header_y = page.page_height * layout_info.header_boundary
        footer_y = page.page_height * layout_info.footer_boundary
        
        block_id = 0
        for raw_block in blocks:
            text_block = TextBlock(
                id=f"p{raw_block.page_number}-b{block_id}",
                page_number=raw_block.page_number,
                text=raw_block.text,
                bbox=raw_block.bbox,
                font_size=raw_block.font_size,
                font_name=raw_block.font_name
            )
            block_id += 1
            
            center_y = raw_block.center_y
            
            if center_y < header_y or center_y > footer_y:
                page.other_blocks.append(text_block)
            else:
                # All content goes to left column
                page.left_column_blocks.append(text_block)
        
        page.raw_left_text = "\n".join(b.text for b in page.left_column_blocks)
        page.raw_right_text = ""  # No right column

# Use it
parser = ParserFactory.create_custom(
    extraction=PyMuPDFExtractor(config),
    layout=SingleColumnLayoutDetector(config),  # Custom layout
    analysis=DefaultHeuristicAnalyzer(config),
    config=config
)

orchestrator = Orchestrator(parser=parser)
```

---

## Creating Custom Heuristic Strategy

Create a minimal heuristic analyzer with only specific heuristics:

```python
from typing import List, Callable
from qna_orchestrator.qna_heuristics.heuristics.patterns import (
    detect_question_start_enhanced,
    detect_answer_boundaries
)

class MinimalHeuristicAnalyzer:
    """Only apply question and answer detection - skip other heuristics."""
    
    def __init__(self, config):
        self.config = config
        self.heuristics = [
            detect_question_start_enhanced,
            detect_answer_boundaries,
        ]
    
    def analyze_blocks(self, blocks, page, config):
        """Apply minimal set of heuristics."""
        if not blocks:
            return
        
        # Calculate basic metrics
        import statistics
        median_spacing = 5.0
        if len(blocks) > 1:
            gaps = [blocks[i].bbox[1] - blocks[i-1].bbox[3] 
                   for i in range(1, len(blocks))]
            median_spacing = statistics.median(gaps) if gaps else 5.0
        
        min_x = min(b.bbox[0] for b in blocks)
        median_font_size = 12.0
        
        # Apply heuristics
        from qna_orchestrator.qna_heuristics.data_models import AnalysisContext
        
        for i, block in enumerate(blocks):
            prev_block = blocks[i-1] if i > 0 else None
            
            context = AnalysisContext(
                current_block=block,
                previous_block=prev_block,
                all_blocks_in_scope=blocks,
                scope_median_spacing=median_spacing,
                scope_min_x=min_x,
                scope_median_font_size=median_font_size,
                config=config,
                page_data=page,
                previous_analysis=None
            )
            
            for heuristic_func in self.heuristics:
                result = heuristic_func(context)
                if result:
                    block.analysis_results.append(result)
    
    def get_heuristics(self) -> List[Callable]:
        return self.heuristics

# Use it
parser = ParserFactory.create_custom(
    extraction=PyMuPDFExtractor(config),
    layout=TwoColumnLayoutDetector(config),
    analysis=MinimalHeuristicAnalyzer(config),  # Custom analysis
    config=config
)
```

---

## Combining Custom Strategies

Mix and match different custom strategies:

```python
from qna_orchestrator.qna_heuristics.config import get_config
from qna_orchestrator.qna_heuristics.parser_factory import ParserFactory
from qna_orchestrator.qna_heuristics.orchestrator import Orchestrator

# Import default implementations
from qna_orchestrator.qna_heuristics.strategies.implementations import (
    PyMuPDFExtractor,
    TwoColumnLayoutDetector,
    DefaultHeuristicAnalyzer
)

config = get_config()

# Scenario 1: Single-column PDF with aggressive heuristics
single_col_parser = ParserFactory.create_custom(
    extraction=PyMuPDFExtractor(config),
    layout=SingleColumnLayoutDetector(config),  # Custom
    analysis=AggressiveHeuristicAnalyzer(config),  # Custom
    config=config
)

# Scenario 2: Complex PDF with pdfplumber + custom heuristics
complex_parser = ParserFactory.create_custom(
    extraction=PDFPlumberExtractor(config),  # Custom
    layout=TwoColumnLayoutDetector(config),  # Default
    analysis=MinimalHeuristicAnalyzer(config),  # Custom
    config=config
)

# Use different parsers for different documents
orchestrator1 = Orchestrator(parser=single_col_parser)
mcqs1 = orchestrator1.run("textbook.pdf")

orchestrator2 = Orchestrator(parser=complex_parser)
mcqs2 = orchestrator2.run("exam.pdf")
```

---

## Real-World Examples

### Example 1: Vision-Based Extraction (LayoutLM)

```python
from transformers import LayoutLMv3Processor, LayoutLMv3Model
from PIL import Image
import torch

class LayoutLMExtractor:
    """Vision-based extraction using LayoutLM for complex layouts."""
    
    def __init__(self, config):
        self.config = config
        self.processor = LayoutLMv3Processor.from_pretrained(
            "microsoft/layoutlmv3-base"
        )
        self.model = LayoutLMv3Model.from_pretrained(
            "microsoft/layoutlmv3-base"
        )
    
    def extract_blocks(self, pdf_path: str, page_num: int) -> List[RawTextBlock]:
        # Convert PDF page to image
        # Use LayoutLM for text detection and extraction
        # Return RawTextBlock objects
        pass  # Implementation details...
    
    # ... other methods

# Use for documents with complex layouts (tables, forms, etc.)
parser = ParserFactory.create_custom(
    extraction=LayoutLMExtractor(config),
    layout=VisionLayoutDetector(config),
    analysis=DefaultHeuristicAnalyzer(config),
    config=config
)
```

### Example 2: Three-Column Layout

```python
class ThreeColumnLayoutDetector:
    """Detect 3-column layouts."""
    
    def detect_layout(self, page, blocks):
        # Find two separators
        separators = self._find_two_separators(page, blocks)
        
        return LayoutInfo(
            column_count=3,
            column_separators=separators,
            detected_layout_type="three_column"
        )
    
    def _find_two_separators(self, page, blocks):
        # Analyze text distribution to find 2 gaps
        # Return [separator1_x, separator2_x]
        pass
```

### Example 3: Custom Heuristic for Specific Exam Format

```python
def detect_iit_jee_format(context):
    """Custom heuristic for IIT JEE exam format."""
    block = context.current_block
    
    # IIT JEE has specific patterns like "SECTION-A", "Paragraph Questions"
    if "SECTION" in block.text.upper():
        return {
            "heuristic_name": "iit_jee_format",
            "is_section_header": True,
            "section_name": block.text.strip()
        }
    
    # Multi-correct questions marked with "*"
    if block.text.strip().startswith("*"):
        return {
            "heuristic_name": "iit_jee_format",
            "is_multi_correct": True
        }
    
    return None

class IITJEEHeuristicAnalyzer(DefaultHeuristicAnalyzer):
    """Extends default analyzer with IIT JEE specific heuristics."""
    
    def __init__(self, config):
        super().__init__(config)
        # Add custom heuristic
        self.heuristics.append(detect_iit_jee_format)
```

---

## Best Practices

### 1. Start with Default, Customize as Needed
```python
# Start simple
orchestrator = Orchestrator()  # Uses all defaults

# Then customize only what you need
custom_parser = ParserFactory.create_custom(
    extraction=PyMuPDFExtractor(config),  # Keep default
    layout=SingleColumnLayoutDetector(config),  # Change this
    analysis=DefaultHeuristicAnalyzer(config),  # Keep default
    config=config
)
```

### 2. Test Custom Strategies Independently
```python
# Test extraction
extractor = MyCustomExtractor(config)
blocks = extractor.extract_blocks("test.pdf", 0)
print(f"Extracted {len(blocks)} blocks")

# Test layout
detector = MyCustomLayoutDetector(config)
layout_info = detector.detect_layout(page, blocks)
print(f"Detected {layout_info.column_count} columns")
```

### 3. Reuse Existing Components
```python
# Don't rewrite everything - extend existing strategies
from qna_orchestrator.qna_heuristics.strategies.implementations import (
    PyMuPDFExtractor,
    DefaultHeuristicAnalyzer
)

class MyEnhancedExtractor(PyMuPDFExtractor):
    """Extends PyMuPDF with preprocessing."""
    
    def extract_blocks(self, pdf_path, page_num):
        blocks = super().extract_blocks(pdf_path, page_num)
        # Add your preprocessing
        return self._preprocess(blocks)
```

### 4. Document Your Custom Strategies
```python
class CustomStrategy:
    """
    Brief description.
    
    Use case: When to use this strategy
    Pros: What it does well
    Cons: Limitations
    
    Example:
        strategy = CustomStrategy(config)
        result = strategy.process(data)
    """
```

---

## Troubleshooting

### Custom Strategy Not Working?

1. **Check Protocol Compliance**: Ensure your class implements all required methods
   ```python
   # Use type hints to catch issues early
   from qna_orchestrator.qna_heuristics.strategies import TextExtractionStrategy
   
   class MyExtractor:  # Implements TextExtractionStrategy
       def extract_blocks(self, pdf_path: str, page_num: int) -> List[RawTextBlock]:
           ...
   ```

2. **Test in Isolation**: Test your strategy before integrating
   ```python
   extractor = MyExtractor(config)
   print(extractor.get_page_count("test.pdf"))  # Should work
   ```

3. **Check Return Types**: Ensure you're returning the correct data structures
   ```python
   # Must return List[RawTextBlock], not List[dict]
   blocks = extractor.extract_blocks("test.pdf", 0)
   assert all(isinstance(b, RawTextBlock) for b in blocks)
   ```

---

## Next Steps

- See `qna_orchestrator/qna_heuristics/strategies/implementations/` for reference implementations
- Check `docs/2025-11-24_composable_parser_architecture.md` for architecture details
- Run `test_composable_parser.py` to see the parser in action

---

**Questions or issues?** Check the strategy interfaces in `qna_orchestrator/qna_heuristics/strategies/` for detailed documentation.
