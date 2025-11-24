# Composable Parser Architecture Implementation Plan

**Date:** 2025-11-24  
**Status:** Planning Phase  
**Goal:** Extend the QnA orchestrator to support composable parsers with different heuristic combinations

---

## Executive Summary

This document outlines the architecture and implementation plan for extending the `qna_orchestrator` to support **composable parsers**. The new architecture will allow users to:

1. Mix and match different PDF extraction methods (PyMuPDF, pdfplumber, LayoutLM)
2. Configure different layout detection strategies (2-column, 1-column, complex layouts)
3. Compose custom heuristic pipelines for different document types
4. Create parser presets for common scenarios while maintaining flexibility

---

## Current Architecture Analysis

### Existing Components

```
PDFParser (concrete class)
├── Text Extraction: PyMuPDF (fitz)
├── Layout Detection: Dynamic column separator
└── Block Classification: Header/Footer/Left/Right columns

Orchestrator (main controller)
├── Loads heuristics from config
├── Runs analysis with AnalysisContext
└── Uses StructureAssembler for MCQ assembly

Heuristics (individual functions)
├── spacing.py: Spacing analysis
├── question_start.py: Question detection
├── layout.py: Layout analysis
└── patterns.py: Pattern matching
```

### Current Limitations

1. **Hardcoded extraction**: Only PyMuPDF is supported
2. **Fixed layout strategy**: 2-column detection only
3. **Monolithic parser**: Cannot easily swap extraction methods
4. **Heuristics coupling**: Heuristics are loaded dynamically but not composable
5. **Limited extensibility**: Adding new parser types requires forking the codebase

---

## Proposed Architecture

### Overview: Hybrid Strategy + Pipeline Pattern

We'll implement a **3-layer architecture**:

1. **Strategy Layer**: Pluggable components for extraction, layout, and analysis
2. **Pipeline Layer**: Sequential processing stages with clear interfaces
3. **Factory Layer**: Convenience constructors for common parser configurations

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Parser Factory                            │
│  (Creates preconfigured parsers for common use cases)       │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│                 ComposableParser                             │
│  (Orchestrates strategies and pipeline stages)              │
└───────────┬─────────────┬──────────────┬────────────────────┘
            │             │              │
            ▼             ▼              ▼
    ┌───────────┐  ┌──────────┐  ┌─────────────┐
    │  Text     │  │  Layout  │  │  Heuristic  │
    │Extraction │  │Detection │  │  Analysis   │
    │ Strategy  │  │ Strategy │  │  Strategy   │
    └───────────┘  └──────────┘  └─────────────┘
```

---

## Implementation Phases

### Phase 1: Define Strategy Interfaces ✓ (This PR)

**Goal:** Create protocol definitions for all pluggable components

**Files to Create:**
- `qna_orchestrator/qna_heuristics/strategies/__init__.py`
- `qna_orchestrator/qna_heuristics/strategies/extraction.py`
- `qna_orchestrator/qna_heuristics/strategies/layout.py`
- `qna_orchestrator/qna_heuristics/strategies/analysis.py`

**Interfaces:**

1. **TextExtractionStrategy**
   ```python
   class TextExtractionStrategy(Protocol):
       def extract_blocks(self, pdf_path: str, page_num: int) -> List[RawTextBlock]
       def get_page_dimensions(self, pdf_path: str, page_num: int) -> Tuple[float, float]
       def get_page_count(self, pdf_path: str) -> int
   ```

2. **LayoutDetectionStrategy**
   ```python
   class LayoutDetectionStrategy(Protocol):
       def detect_layout(self, page: Page, blocks: List[TextBlock]) -> LayoutInfo
       def classify_blocks(self, page: Page, blocks: List[TextBlock], layout: LayoutInfo) -> None
   ```

3. **HeuristicAnalysisStrategy**
   ```python
   class HeuristicAnalysisStrategy(Protocol):
       def analyze_blocks(self, blocks: List[TextBlock], page: Page, config: Dict) -> None
       def get_heuristics(self) -> List[Callable]
   ```

**Data Models:**
- `RawTextBlock`: Pre-processing text block (before layout classification)
- `LayoutInfo`: Contains layout metadata (column boundaries, regions, etc.)

**Deliverables:**
- ✅ Protocol definitions
- ✅ Type hints and documentation
- ✅ Data model updates

---

### Phase 2: Implement Default Strategies

**Goal:** Convert existing PDFParser logic into strategy implementations

**Files to Create:**
- `qna_orchestrator/qna_heuristics/strategies/implementations/pymupdf_extractor.py`
- `qna_orchestrator/qna_heuristics/strategies/implementations/two_column_layout.py`
- `qna_orchestrator/qna_heuristics/strategies/implementations/default_heuristic_analyzer.py`

**Implementation Details:**

1. **PyMuPDFExtractor** (TextExtractionStrategy)
   - Extract current `_get_text_blocks()` logic from PDFParser
   - Make it standalone with no dependencies on PDFParser class
   - Add configuration for line-level vs block-level extraction

2. **TwoColumnLayoutDetector** (LayoutDetectionStrategy)
   - Extract `_find_column_separator()` and `_classify_blocks()` from PDFParser
   - Make column detection configurable (threshold, region percentages)
   - Add support for dynamic header/footer detection

3. **DefaultHeuristicAnalyzer** (HeuristicAnalysisStrategy)
   - Wrapper around existing heuristic loading mechanism from Orchestrator
   - Load heuristics from config
   - Apply heuristics with AnalysisContext

**Deliverables:**
- ✅ Three concrete strategy implementations
- ✅ Unit tests for each strategy
- ✅ Backward compatibility with existing code

---

### Phase 3: Create ComposableParser

**Goal:** Build the main parser that uses strategies

**Files to Create:**
- `qna_orchestrator/qna_heuristics/composable_parser.py`

**Implementation:**

```python
class ComposableParser(BaseParser):
    def __init__(
        self,
        extraction_strategy: TextExtractionStrategy,
        layout_strategy: LayoutDetectionStrategy,
        analysis_strategy: HeuristicAnalysisStrategy,
        config: Dict
    ):
        self.extraction = extraction_strategy
        self.layout = layout_strategy
        self.analysis = analysis_strategy
        self.config = config
    
    def parse(self, pdf_path: str) -> Document:
        doc = Document(pdf_path=pdf_path)
        page_count = self.extraction.get_page_count(pdf_path)
        
        for page_num in range(page_count):
            # Extract raw blocks
            raw_blocks = self.extraction.extract_blocks(pdf_path, page_num)
            width, height = self.extraction.get_page_dimensions(pdf_path, page_num)
            
            # Create page object
            page = Page(page_number=page_num + 1, page_width=width, page_height=height)
            
            # Detect layout
            layout_info = self.layout.detect_layout(page, raw_blocks)
            
            # Classify blocks into regions
            self.layout.classify_blocks(page, raw_blocks, layout_info)
            
            # Analyze blocks with heuristics
            self.analysis.analyze_blocks(page.left_column_blocks, page, self.config)
            self.analysis.analyze_blocks(page.right_column_blocks, page, self.config)
            
            doc.pages.append(page)
        
        return doc
```

**Features:**
- Constructor injection for all strategies
- Clear separation between extraction → layout → analysis
- Extensible for new strategies without modifying core logic

**Deliverables:**
- ✅ ComposableParser implementation
- ✅ Integration tests with existing Document/MCQ flow
- ✅ Performance benchmarks vs current PDFParser

---

### Phase 4: Build Parser Factory

**Goal:** Provide convenience methods for common parser configurations

**Files to Create:**
- `qna_orchestrator/qna_heuristics/parser_factory.py`

**Implementation:**

```python
class ParserFactory:
    @staticmethod
    def create_default(config: Dict) -> ComposableParser:
        """Current PDFParser behavior"""
        return ComposableParser(
            extraction_strategy=PyMuPDFExtractor(config),
            layout_strategy=TwoColumnLayoutDetector(config),
            analysis_strategy=DefaultHeuristicAnalyzer(config),
            config=config
        )
    
    @staticmethod
    def create_single_column(config: Dict) -> ComposableParser:
        """For single-column documents"""
        return ComposableParser(
            extraction_strategy=PyMuPDFExtractor(config),
            layout_strategy=SingleColumnLayoutDetector(config),
            analysis_strategy=DefaultHeuristicAnalyzer(config),
            config=config
        )
    
    @staticmethod
    def create_vision_based(config: Dict) -> ComposableParser:
        """Uses LayoutLM or similar vision models"""
        return ComposableParser(
            extraction_strategy=LayoutLMExtractor(config),
            layout_strategy=VisionLayoutDetector(config),
            analysis_strategy=DefaultHeuristicAnalyzer(config),
            config=config
        )
    
    @staticmethod
    def create_custom(
        extraction: TextExtractionStrategy,
        layout: LayoutDetectionStrategy,
        analysis: HeuristicAnalysisStrategy,
        config: Dict
    ) -> ComposableParser:
        """Full control for advanced users"""
        return ComposableParser(extraction, layout, analysis, config)
```

**Configuration Support:**
```yaml
# In config.yaml
parser:
  type: "default"  # or "single_column", "vision_based", "custom"
  extraction:
    provider: "pymupdf"  # or "pdfplumber", "layoutlm"
  layout:
    detector: "two_column"  # or "single_column", "vision"
  analysis:
    heuristics: ["spacing", "question_start", "layout"]
```

**Deliverables:**
- ✅ ParserFactory with presets
- ✅ YAML configuration support
- ✅ Documentation and usage examples

---

### Phase 5: Alternative Strategy Implementations

**Goal:** Implement additional extraction and layout strategies

**Files to Create:**
- `qna_orchestrator/qna_heuristics/strategies/implementations/pdfplumber_extractor.py`
- `qna_orchestrator/qna_heuristics/strategies/implementations/single_column_layout.py`
- `qna_orchestrator/qna_heuristics/strategies/implementations/layoutlm_extractor.py` (optional)

**1. PDFPlumberExtractor**
- Alternative to PyMuPDF
- Better table detection
- More accurate text positioning for some PDFs

**2. SingleColumnLayoutDetector**
- No column splitting
- Simple top-to-bottom reading order
- Useful for textbooks, reports

**3. LayoutLMExtractor** (Future/Optional)
- Vision-based document understanding
- Uses pre-trained models (LayoutLMv3, etc.)
- Better for complex layouts

**Deliverables:**
- ✅ At least 2 alternative implementations
- ✅ Comparison benchmarks
- ✅ Migration guide from current implementation

---

### Phase 6: Update Orchestrator Integration

**Goal:** Make Orchestrator use ComposableParser with backward compatibility

**Files to Modify:**
- `qna_orchestrator/qna_heuristics/orchestrator.py`

**Changes:**

```python
class Orchestrator:
    def __init__(self, config_overrides: Optional[Dict] = None, parser: Optional[BaseParser] = None):
        self.config = deepcopy(get_config())
        if config_overrides:
            self.config.update(config_overrides)
        
        # NEW: Accept custom parser or create default
        if parser:
            self.parser = parser
        else:
            self.parser = ParserFactory.create_default(self.config)
        
        os.makedirs(self.config["OUTPUT_DIR"], exist_ok=True)
    
    def run(self, pdf_path: str) -> List[MCQ]:
        # Use self.parser instead of PDFParser
        doc = self.parser.parse(pdf_path)
        # ... rest of the logic remains the same
```

**Backward Compatibility:**
- Existing code without parser argument continues to work
- Config-based parser selection via ParserFactory
- Current PDFParser can coexist during migration

**Deliverables:**
- ✅ Updated Orchestrator
- ✅ Backward compatibility tests
- ✅ Migration examples

---

### Phase 7: Documentation & Examples

**Goal:** Comprehensive documentation for new architecture

**Files to Create:**
- `docs/architecture/composable_parser.md`
- `docs/examples/custom_parser_example.py`
- `docs/examples/parser_comparison.py`
- `docs/migration_guide.md`

**Documentation Sections:**
1. Architecture overview
2. Strategy pattern explanation
3. Creating custom strategies
4. Parser factory usage
5. Performance considerations
6. Migration from PDFParser to ComposableParser

**Example Use Cases:**
```python
# Example 1: Use preset
parser = ParserFactory.create_default(config)

# Example 2: Custom combination
parser = ComposableParser(
    extraction_strategy=PDFPlumberExtractor(config),
    layout_strategy=TwoColumnLayoutDetector(config),
    analysis_strategy=CustomHeuristicAnalyzer(["spacing", "bold_detection"]),
    config=config
)

# Example 3: Vision-based for complex layouts
parser = ParserFactory.create_vision_based(config)
```

**Deliverables:**
- ✅ Complete architecture documentation
- ✅ 5+ example scripts
- ✅ API reference
- ✅ Migration guide

---

## Testing Strategy

### Unit Tests
- Test each strategy interface implementation independently
- Mock dependencies for isolated testing
- Coverage target: 90%+

### Integration Tests
- Test ComposableParser with different strategy combinations
- Verify backward compatibility with existing PDFs
- Test against sample PDFs with known MCQ structures

### Performance Tests
- Benchmark extraction speed for different strategies
- Compare memory usage
- Regression tests vs current PDFParser

### Test Files to Create
```
tests/strategies/
├── test_extraction_strategies.py
├── test_layout_strategies.py
├── test_analysis_strategies.py
tests/integration/
├── test_composable_parser.py
├── test_parser_factory.py
├── test_orchestrator_integration.py
tests/performance/
└── test_parser_benchmarks.py
```

---

## Configuration Schema

### New Config Structure

```yaml
parser:
  # Parser type preset
  type: "default"  # Options: default, single_column, vision_based, custom
  
  # Text Extraction Configuration
  extraction:
    provider: "pymupdf"  # Options: pymupdf, pdfplumber, layoutlm
    options:
      line_level: true  # Extract at line level vs block level
      preserve_whitespace: false
      
  # Layout Detection Configuration
  layout:
    detector: "two_column"  # Options: two_column, single_column, vision
    options:
      column_separator_threshold: 0.05  # 5% of page width
      header_region_percent: 0.1
      footer_region_percent: 0.9
      
  # Heuristic Analysis Configuration
  analysis:
    strategy: "default"  # Options: default, aggressive, conservative, custom
    heuristics:
      - spacing
      - question_start
      - layout
      - patterns
    options:
      parallel_processing: false  # Future: parallel heuristic execution
```

---

## Migration Path

### For Existing Users

**No changes required** - the default behavior will match current PDFParser:
```python
# This continues to work
orchestrator = Orchestrator(config)
mcqs = orchestrator.run("exam.pdf")
```

### For Advanced Users

**Opt-in to new features**:
```python
# Use factory
parser = ParserFactory.create_single_column(config)
orchestrator = Orchestrator(config, parser=parser)

# Or full custom
custom_parser = ComposableParser(
    extraction_strategy=MyCustomExtractor(),
    layout_strategy=MyCustomLayout(),
    analysis_strategy=DefaultHeuristicAnalyzer(config),
    config=config
)
orchestrator = Orchestrator(config, parser=custom_parser)
```

### Deprecation Timeline

- **Phase 1-3**: New architecture introduced, PDFParser unchanged
- **Phase 4-5**: PDFParser marked as "legacy" in docs
- **Phase 6**: PDFParser refactored to use ComposableParser internally
- **Future**: PDFParser removed (major version bump)

---

## Success Criteria

### Functional Requirements
- ✅ Existing PDFs parse with identical results
- ✅ Can swap extraction strategies without code changes
- ✅ Can add new strategies without modifying core code
- ✅ Parser factory supports 3+ presets

### Non-Functional Requirements
- ✅ Performance within 10% of current implementation
- ✅ Code coverage ≥90% for new components
- ✅ Zero breaking changes for existing users
- ✅ Documentation completeness score ≥95%

### Developer Experience
- ✅ New strategy implementation takes <2 hours
- ✅ Clear examples for all common use cases
- ✅ Type hints enable IDE autocomplete
- ✅ Error messages guide users to solutions

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Performance degradation | High | Low | Benchmark each phase; optimize hot paths |
| Breaking existing code | High | Medium | Maintain backward compatibility; extensive testing |
| Over-engineering | Medium | Medium | Implement incrementally; gather feedback |
| Strategy explosion | Low | High | Document best practices; provide good presets |
| Adoption resistance | Medium | Low | Clear migration guide; maintain old API |

---

## Open Questions

1. **Heuristic Composition**: Should heuristics be chainable/pipelines themselves?
2. **Async Support**: Should strategies support async extraction for large PDFs?
3. **Caching**: Should we cache extraction results for repeated parsing?
4. **Telemetry**: Should we add metrics/logging for strategy performance?
5. **Plugin System**: Should strategies be loadable from external packages?

---

## Timeline Estimate

| Phase | Estimated Time | Dependencies |
|-------|----------------|--------------|
| Phase 1: Interfaces | 2-3 days | None |
| Phase 2: Default Strategies | 3-4 days | Phase 1 |
| Phase 3: ComposableParser | 2-3 days | Phase 2 |
| Phase 4: Parser Factory | 1-2 days | Phase 3 |
| Phase 5: Alternative Strategies | 4-5 days | Phase 3 |
| Phase 6: Orchestrator Integration | 2-3 days | Phase 4 |
| Phase 7: Documentation | 3-4 days | Phase 6 |
| **Total** | **17-24 days** | |

---

## Next Steps

### Immediate (This Session)
1. ✅ Create this planning document
2. ✅ Implement Phase 1: Strategy interfaces
3. Review and get feedback

### Short-term (Next Session)
1. Implement Phase 2: Default strategies
2. Write unit tests
3. Create comparison benchmarks

### Medium-term (This Week)
1. Complete Phases 3-4
2. Integration testing
3. Create usage examples

---

## References

- **Current Codebase**: `qna_orchestrator/qna_heuristics/`
- **Design Patterns**: Strategy Pattern, Factory Pattern, Pipeline Pattern
- **Similar Projects**: pdfplumber, camelot-py, layout-parser

---

**End of Plan**
