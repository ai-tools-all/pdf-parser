# in parsers.py
from typing import List, Dict, Any, Optional, Callable
from qna_orchestrator.qna_heuristics.data_models import Document, Page, TextBlock, AnalysisContext, BaseParser
from qna_orchestrator.qna_heuristics.pdf_parser import PDFParser
import statistics
import importlib

# Marker text found on Vision IAS instruction pages
INSTRUCTION_PAGE_MARKER = "IMMEDIATELY AFTER THE COMMENCEMENT OF THE EXAMINATION"

class HeuristicBasedParser(BaseParser):
    """
    A parser that combines PDF text extraction with configurable heuristics.

    This parser extracts text blocks from PDFs and applies a series of heuristics
    to analyze and classify the content for MCQ extraction.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pdf_parser = PDFParser(config)
        self.heuristics = self._load_heuristics()
        self.page_filter = self._get_page_filter()

    def _get_page_filter(self) -> Optional[List[int]]:
        """Get list of pages to skip during processing."""
        return self.config.get("SKIP_PAGES")

    def _is_instruction_page_from_pdf(self, pdf_path: str, page_num: int = 0) -> bool:
        """Check if a page is an instruction page by reading raw PDF text (before noise filtering)."""
        import fitz
        try:
            doc = fitz.open(pdf_path)
            if page_num < len(doc):
                page = doc[page_num]
                raw_text = page.get_text("text")
                doc.close()
                return INSTRUCTION_PAGE_MARKER.lower() in raw_text.lower()
            doc.close()
        except Exception:
            pass
        return False

    def _apply_page_filter(self, doc: Document) -> Document:
        """Filter pages based on SKIP_PAGES and PAGE_RANGE."""
        # 1. Handle SKIP_PAGES (existing logic)
        pages_to_keep = [p for p in doc.pages if p.page_number not in (self.page_filter or [])]

        # 2. Handle PAGE_RANGE (New Logic)
        page_range = self.config.get("PAGE_RANGE")
        if page_range and isinstance(page_range, (list, tuple)) and len(page_range) == 2:
            start, end = page_range
            # Filter pages strictly within [start, end] inclusive
            pages_to_keep = [p for p in pages_to_keep if start <= p.page_number <= end]

        return Document(pdf_path=doc.pdf_path, pages=pages_to_keep)

    def _load_heuristics(self) -> List[Callable]:
        """Load heuristics from configuration."""
        loaded_funcs = []
        for path in self.config.get("ACTIVE_HEURISTICS", []):
            module_path, func_name = path.rsplit('.', 1)
            try:
                module = importlib.import_module(module_path)
                func = getattr(module, func_name)
                loaded_funcs.append(func)
            except (ImportError, AttributeError) as e:
                print(f"Warning: Could not load heuristic '{path}': {e}")
        return loaded_funcs

    def parse(self, pdf_path: str) -> Document:
        """
        Parse a PDF document and apply heuristics to analyze content.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Document: Parsed and analyzed document with heuristic results
        """
        # Phase 1: Extract text blocks
        doc = self.pdf_parser.parse(pdf_path)

        # Phase 2: Auto-detect instruction page if page 1 is in SKIP_PAGES
        if self.page_filter and 1 in self.page_filter and doc.pages:
            if not self._is_instruction_page_from_pdf(pdf_path, page_num=0):
                # Page 1 is NOT an instruction page - don't skip it
                self.page_filter = [p for p in self.page_filter if p != 1]

        # Phase 3: Apply page filtering if configured
        if self.page_filter:
            doc = self._apply_page_filter(doc)

        # Phase 4: Apply heuristics to analyze content
        analyzed_doc = self._apply_heuristics(doc)

        return analyzed_doc

    def _apply_heuristics(self, doc: Document) -> Document:
        """Apply all configured heuristics to the document."""
        analyzed_doc = Document(pdf_path=doc.pdf_path, pages=[])

        for page in doc.pages:
            analyzed_page = Page(
                page_number=page.page_number,
                page_width=page.page_width,
                page_height=page.page_height,
                left_column_blocks=[],
                right_column_blocks=[],
                other_blocks=page.other_blocks.copy(),
                raw_left_text=page.raw_left_text,
                raw_right_text=page.raw_right_text
            )

            # Analyze left and right columns separately
            analyzed_page.left_column_blocks = self._analyze_blocks(
                page.left_column_blocks, page
            )
            analyzed_page.right_column_blocks = self._analyze_blocks(
                page.right_column_blocks, page
            )

            analyzed_doc.pages.append(analyzed_page)

        return analyzed_doc

    def _analyze_blocks(self, blocks: List[TextBlock], page: Page) -> List[TextBlock]:
        """Apply heuristics to a list of blocks within a column scope."""
        if not blocks:
            return blocks

        # Create analyzed copies
        analyzed_blocks = [TextBlock(**block.__dict__) for block in blocks]
        for block in analyzed_blocks:
            block.analysis_results = []  # Reset analysis results

        # Pre-calculate scope-wide metrics
        cfg = self.config.get('HEURISTICS', {}).get('SPACING', {})
        gaps = []
        for i in range(1, len(analyzed_blocks)):
            gap = analyzed_blocks[i].bbox[1] - analyzed_blocks[i-1].bbox[3]
            gaps.append(gap)

        normal_gaps = [g for g in gaps if cfg.get('MIN_GAP_FOR_NORMAL_SPACING', 0.5) < g < cfg.get('MAX_GAP_FOR_NORMAL_SPACING', 20.0)]
        median_spacing = statistics.median(normal_gaps) if normal_gaps else 5.0

        min_x = min(b.bbox[0] for b in analyzed_blocks)

        # Calculate median font size
        font_sizes = [b.font_size for b in analyzed_blocks if b.font_size > 0]
        median_font_size = statistics.median(font_sizes) if font_sizes else 12.0

        previous_analysis = None
        for i, block in enumerate(analyzed_blocks):
            prev_block = analyzed_blocks[i-1] if i > 0 else None
            context = AnalysisContext(
                current_block=block,
                previous_block=prev_block,
                all_blocks_in_scope=analyzed_blocks,
                scope_median_spacing=median_spacing,
                scope_min_x=min_x,
                scope_median_font_size=median_font_size,
                config=self.config,
                page_data=page,
                previous_analysis=previous_analysis
            )

            # Reset for the current block
            current_block_analysis = {}
            for heuristic_func in self.heuristics:
                result = heuristic_func(context)
                if result:
                    block.analysis_results.append(result)
                    current_block_analysis.update(result)

            previous_analysis = current_block_analysis

        return analyzed_blocks


class CompositeParser(BaseParser):
    """
    A parser that combines multiple parsers to process a document.

    This allows for different parsing strategies to be applied sequentially
    or in parallel, with results merged or selected based on configuration.
    """

    def __init__(self, parsers: List[BaseParser], merge_strategy: str = "sequential"):
        """
        Initialize composite parser.

        Args:
            parsers: List of parsers to combine
            merge_strategy: How to merge results ("sequential", "parallel", "vote")
        """
        self.parsers = parsers
        self.merge_strategy = merge_strategy

    def parse(self, pdf_path: str) -> Document:
        """
        Parse document using all configured parsers and merge results.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Document: Parsed document with merged analysis results
        """
        if not self.parsers:
            raise ValueError("No parsers configured")

        if self.merge_strategy == "sequential":
            return self._parse_sequential(pdf_path)
        elif self.merge_strategy == "parallel":
            return self._parse_parallel(pdf_path)
        else:
            raise ValueError(f"Unknown merge strategy: {self.merge_strategy}")

    def _parse_sequential(self, pdf_path: str) -> Document:
        """Apply parsers sequentially, with each building on the previous."""
        # Start with the first parser
        result_doc = self.parsers[0].parse(pdf_path)

        # Apply subsequent parsers to refine results
        for parser in self.parsers[1:]:
            # For now, just take the result from the last parser
            # In a more sophisticated implementation, we could merge results
            result_doc = parser.parse(pdf_path)

        return result_doc

    def _parse_parallel(self, pdf_path: str) -> Document:
        """Apply all parsers independently and merge results."""
        if not self.parsers:
            raise ValueError("No parsers to run in parallel")

        # Run all parsers
        results = [parser.parse(pdf_path) for parser in self.parsers]

        # For now, return the result from the first parser
        # In a more sophisticated implementation, we could merge analysis results
        return results[0]