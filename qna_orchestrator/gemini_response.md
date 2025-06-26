Of course. Here is the complete, runnable Python code for the proposed architecture, organized into the specified files.

---
<file> config.py </file>
<code>
```python
# in config.py

DEFAULT_CONFIG = {
    "DEBUG_SAVE_INTERMEDIATE": True,
    "OUTPUT_DIR": "./output",
    "PDF_PATH": "./data_dir/document.pdf", # Default path, can be overridden

    # List of heuristic functions to apply during the analysis phase
    # The orchestrator will dynamically import these.
    "ACTIVE_HEURISTICS": [
        "heuristics.spacing.analyze_vertical_break",
        "heuristics.patterns.analyze_question_number",
        "heuristics.patterns.analyze_option_letter",
        "heuristics.patterns.analyze_answer_marker",
        "heuristics.layout.analyze_indentation",
    ],

    # Parameters for the PDF Parser
    "PARSER": {
        "HEADER_REGION_PERCENT": 0.12,
        "FOOTER_REGION_PERCENT": 0.90,
    },

    # Parameters for Heuristics, organized by module
    "HEURISTICS": {
        "SPACING": {
            # A gap is a "break" if it's > N times the normal line spacing
            "BREAK_THRESHOLD_MULTIPLIER": 1.7,
            # Ignore tiny gaps when calculating normal spacing
            "MIN_GAP_FOR_NORMAL_SPACING": 0.5,
            # Ignore huge gaps (likely section breaks) for normal spacing
            "MAX_GAP_FOR_NORMAL_SPACING": 20.0,
        },
        "LAYOUT": {
            # How much horizontal space defines an indentation (in points)
            "INDENTATION_THRESHOLD": 15.0,
        },
        "PATTERNS": {
            "REGEX_QUESTION": r'^\s*(\d+)\.',
            "REGEX_OPTION": r'^\s*\(([a-zA-Z])\)',
            "REGEX_ANSWER": r'^\s*Ans:\s*\(?([a-zA-Z])\)?',
        }
    }
}
```
</code>

---
<file> data_models.py </file>
<code>
```python
# in data_models.py
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional

@dataclass
class TextBlock:
    id: str  # e.g., "p1-b23"
    page_number: int
    text: str
    bbox: Tuple[float, float, float, float]
    # This list will be populated by the analysis phase
    analysis_results: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class Page:
    page_number: int
    page_width: float
    page_height: float
    left_column_blocks: List[TextBlock] = field(default_factory=list)
    right_column_blocks: List[TextBlock] = field(default_factory=list)
    other_blocks: List[TextBlock] = field(default_factory=list) # Header, footer, etc.
    # Raw content is preserved here for inspection
    raw_left_text: str = ""
    raw_right_text: str = ""

@dataclass
class Document:
    pdf_path: str
    pages: List[Page] = field(default_factory=list)

@dataclass
class MCQ:
    question_number: int
    question_text: str
    options: Dict[str, str] = field(default_factory=dict)
    answer: Optional[str] = None
    explanation: Optional[str] = None

class AnalysisContext:
    """Provides a heuristic with surrounding information."""
    def __init__(
        self,
        current_block: TextBlock,
        previous_block: Optional[TextBlock],
        all_blocks_in_scope: List[TextBlock],
        scope_median_spacing: float,
        scope_min_x: float,
        config: Dict[str, Any]
    ):
        self.current_block = current_block
        self.previous_block = previous_block
        self.all_blocks_in_scope = all_blocks_in_scope
        self.scope_median_spacing = scope_median_spacing
        self.scope_min_x = scope_min_x
        self.config = config
```
</code>

---
<file> pdf_parser.py </file>
<code>
```python
# in pdf_parser.py
import fitz  # PyMuPDF
from typing import List, Dict, Tuple
from data_models import Document, Page, TextBlock

class PDFParser:
    def __init__(self, config: Dict):
        self.config = config["PARSER"]

    def parse(self, pdf_path: str) -> Document:
        doc = fitz.open(pdf_path)
        document_obj = Document(pdf_path=pdf_path)

        for page_num, page in enumerate(doc):
            page_obj = Page(
                page_number=page_num + 1,
                page_width=page.rect.width,
                page_height=page.rect.height,
            )

            blocks = self._get_text_blocks(page)
            separator_x = self._find_column_separator(page, blocks)
            self._classify_blocks(page_obj, blocks, separator_x)

            # Generate raw text for inspection
            page_obj.raw_left_text = "\n".join(b.text for b in page_obj.left_column_blocks)
            page_obj.raw_right_text = "\n".join(b.text for b in page_obj.right_column_blocks)

            document_obj.pages.append(page_obj)

        doc.close()
        return document_obj

    def _get_text_blocks(self, page: fitz.Page) -> List[TextBlock]:
        raw_blocks = page.get_text("dict")["blocks"]
        text_blocks = []
        block_idx = 0
        for b in raw_blocks:
            if "lines" not in b:
                continue
            for line in b["lines"]:
                if line["spans"]:
                    text = "".join(span["text"] for span in line["spans"]).strip()
                    if text:
                        text_blocks.append(TextBlock(
                            id=f"p{page.number + 1}-b{block_idx}",
                            page_number=page.number + 1,
                            text=text,
                            bbox=line["bbox"]
                        ))
                        block_idx += 1
        # Sort blocks by reading order (top-to-bottom, left-to-right)
        return sorted(text_blocks, key=lambda b: (b.bbox[1], b.bbox[0]))

    def _find_column_separator(self, page: fitz.Page, blocks: List[TextBlock]) -> float:
        # Simplified heuristic: assume separator is near the middle
        # A more robust implementation would analyze gaps in the x-distribution of text
        return page.rect.width / 2

    def _classify_blocks(self, page_obj: Page, blocks: List[TextBlock], separator_x: float):
        header_y = page_obj.page_height * self.config["HEADER_REGION_PERCENT"]
        footer_y = page_obj.page_height * self.config["FOOTER_REGION_PERCENT"]

        for block in blocks:
            center_y = (block.bbox[1] + block.bbox[3]) / 2
            center_x = (block.bbox[0] + block.bbox[2]) / 2

            if center_y < header_y or center_y > footer_y:
                page_obj.other_blocks.append(block)
            elif center_x < separator_x:
                page_obj.left_column_blocks.append(block)
            else:
                page_obj.right_column_blocks.append(block)
```
</code>

---
<file> heuristics/__init__.py </file>
<code>
```python
# This file can be empty.
# It makes the 'heuristics' directory a Python package.
```
</code>

---
<file> heuristics/spacing.py </file>
<code>
```python
# in heuristics/spacing.py
from typing import Dict, Any, Optional
from data_models import AnalysisContext

def analyze_vertical_break(context: AnalysisContext) -> Optional[Dict[str, Any]]:
    """Identifies if a block is preceded by a large vertical gap."""
    if not context.previous_block:
        return None

    cfg = context.config['HEURISTICS']['SPACING']
    gap = context.current_block.bbox[1] - context.previous_block.bbox[3]
    multiplier = cfg['BREAK_THRESHOLD_MULTIPLIER']
    
    # Use pre-calculated median spacing for efficiency
    median_spacing = context.scope_median_spacing

    if gap > (median_spacing * multiplier):
        return {
            "heuristic_name": "vertical_break",
            "is_break": True,
            "gap_size": round(gap, 2)
        }
    return None
```
</code>

---
<file> heuristics/patterns.py </file>
<code>
```python
# in heuristics/patterns.py
import re
from typing import Dict, Any, Optional
from data_models import AnalysisContext

def analyze_question_number(context: AnalysisContext) -> Optional[Dict[str, Any]]:
    """Checks if a block starts with a question number pattern."""
    regex = context.config['HEURISTICS']['PATTERNS']['REGEX_QUESTION']
    match = re.match(regex, context.current_block.text)
    if match:
        return {
            "heuristic_name": "pattern_match",
            "type": "question_start",
            "value": int(match.group(1))
        }
    return None

def analyze_option_letter(context: AnalysisContext) -> Optional[Dict[str, Any]]:
    """Checks if a block starts with an option letter like (a)."""
    regex = context.config['HEURISTICS']['PATTERNS']['REGEX_OPTION']
    match = re.match(regex, context.current_block.text)
    if match:
        return {
            "heuristic_name": "pattern_match",
            "type": "option",
            "value": match.group(1).lower()
        }
    return None

def analyze_answer_marker(context: AnalysisContext) -> Optional[Dict[str, Any]]:
    """Checks if a block starts with an answer marker like Ans: (c)."""
    regex = context.config['HEURISTICS']['PATTERNS']['REGEX_ANSWER']
    match = re.match(regex, context.current_block.text, re.IGNORECASE)
    if match:
        return {
            "heuristic_name": "pattern_match",
            "type": "answer_marker",
            "value": match.group(1).lower()
        }
    return None
```
</code>

---
<file> heuristics/layout.py </file>
<code>
```python
# in heuristics/layout.py
from typing import Dict, Any, Optional
from data_models import AnalysisContext

def analyze_indentation(context: AnalysisContext) -> Optional[Dict[str, Any]]:
    """Checks if a block is indented relative to the column's minimum x-coordinate."""
    cfg = context.config['HEURISTICS']['LAYOUT']
    indent_threshold = cfg['INDENTATION_THRESHOLD']

    # Use pre-calculated minimum x for the scope
    indentation = context.current_block.bbox[0] - context.scope_min_x

    if indentation > indent_threshold:
        return {
            "heuristic_name": "indentation",
            "is_indented": True,
            "indent_amount": round(indentation, 2)
        }
    return None
```
</code>

---
<file> orchestrator.py </file>
<code>
```python
# in orchestrator.py
import os
import json
import importlib
import statistics
from copy import deepcopy
from typing import Dict, Any, List, Optional
from config import DEFAULT_CONFIG
from data_models import Document, MCQ, TextBlock, AnalysisContext
from pdf_parser import PDFParser

class Orchestrator:
    def __init__(self, config_overrides: Optional[Dict] = None):
        self.config = deepcopy(DEFAULT_CONFIG)
        if config_overrides:
            # A more robust implementation would merge nested dicts
            self.config.update(config_overrides)
        
        self.heuristics = self._load_heuristics()
        os.makedirs(self.config["OUTPUT_DIR"], exist_ok=True)

    def _load_heuristics(self):
        loaded_funcs = []
        for path in self.config["ACTIVE_HEURISTICS"]:
            module_path, func_name = path.rsplit('.', 1)
            try:
                module = importlib.import_module(module_path)
                func = getattr(module, func_name)
                loaded_funcs.append(func)
            except (ImportError, AttributeError) as e:
                print(f"Warning: Could not load heuristic '{path}': {e}")
        return loaded_funcs

    def _save_json(self, data, filename):
        if not self.config["DEBUG_SAVE_INTERMEDIATE"]:
            return
        
        # Custom JSON encoder for dataclasses
        class DataClassEncoder(json.JSONEncoder):
            def default(self, o):
                if hasattr(o, '__dict__'):
                    return o.__dict__
                return super().default(o)
        
        path = os.path.join(self.config["OUTPUT_DIR"], filename)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, cls=DataClassEncoder, indent=2)
        print(f"Saved intermediate file: {path}")

    def run(self, pdf_path: str) -> List[MCQ]:
        # --- Phase 1: Parsing ---
        print("Phase 1: Parsing PDF...")
        parser = PDFParser(self.config)
        doc = parser.parse(pdf_path)
        self._save_json(doc, "01_raw_document.json")

        # --- Phase 2: Analysis ---
        print("Phase 2: Applying heuristics...")
        analyzed_doc = self._run_analysis(doc)
        self._save_json(analyzed_doc, "02_analyzed_document.json")
        
        # --- Phase 3: Assembly ---
        print("Phase 3: Assembling MCQs...")
        assembler = StructureAssembler(self.config)
        mcqs = assembler.assemble(analyzed_doc)
        self._save_json(mcqs, "03_final_mcqs.json")

        print(f"\nExtraction complete. Found {len(mcqs)} MCQs.")
        return mcqs

    def _run_analysis(self, doc: Document) -> Document:
        analyzed_doc = deepcopy(doc)
        for page in analyzed_doc.pages:
            # Analyze left and right columns separately
            self._analyze_scope(page.left_column_blocks)
            self._analyze_scope(page.right_column_blocks)
        return analyzed_doc

    def _analyze_scope(self, blocks: List[TextBlock]):
        if not blocks:
            return
            
        # Pre-calculate scope-wide metrics
        cfg = self.config['HEURISTICS']['SPACING']
        gaps = [blocks[i].bbox[1] - blocks[i-1].bbox[3] for i in range(1, len(blocks))]
        normal_gaps = [g for g in gaps if cfg['MIN_GAP_FOR_NORMAL_SPACING'] < g < cfg['MAX_GAP_FOR_NORMAL_SPACING']]
        median_spacing = statistics.median(normal_gaps) if normal_gaps else 5.0
        min_x = min(b.bbox[0] for b in blocks)

        for i, block in enumerate(blocks):
            prev_block = blocks[i-1] if i > 0 else None
            context = AnalysisContext(
                current_block=block,
                previous_block=prev_block,
                all_blocks_in_scope=blocks,
                scope_median_spacing=median_spacing,
                scope_min_x=min_x,
                config=self.config
            )
            for heuristic_func in self.heuristics:
                result = heuristic_func(context)
                if result:
                    block.analysis_results.append(result)

class StructureAssembler:
    def __init__(self, config):
        self.config = config

    def _get_analysis(self, block: TextBlock, heuristic_name: str, key: str, default=None):
        for result in block.analysis_results:
            if result.get("heuristic_name") == heuristic_name:
                return result.get(key, default)
        return default

    def _is_question_start(self, block: TextBlock) -> bool:
        is_break = self._get_analysis(block, "vertical_break", "is_break", False)
        pattern_type = self._get_analysis(block, "pattern_match", "type")
        return is_break and pattern_type == "question_start"

    def assemble(self, doc: Document) -> List[MCQ]:
        all_blocks = []
        for page in doc.pages:
            all_blocks.extend(page.left_column_blocks)
            all_blocks.extend(page.right_column_blocks)
        # Re-sort globally to handle content flowing across columns/pages
        all_blocks.sort(key=lambda b: (b.page_number, b.bbox[1], b.bbox[0]))
        
        mcqs = []
        current_mcq = None
        current_part = "question" # states: question, option, explanation

        for block in all_blocks:
            if self._is_question_start(block):
                if current_mcq:
                    mcqs.append(current_mcq)
                
                q_num = self._get_analysis(block, "pattern_match", "value")
                current_mcq = MCQ(question_number=q_num, question_text="")
                current_part = "question"

            if not current_mcq:
                continue

            # State machine logic
            pattern_type = self._get_analysis(block, "pattern_match", "type")
            if pattern_type == "option":
                current_part = "option"
            elif pattern_type == "answer_marker":
                current_part = "explanation"
                
            # Append text based on current state
            if current_part == "question":
                # Remove the "1. " part from the text
                text_to_add = re.sub(self.config['HEURISTICS']['PATTERNS']['REGEX_QUESTION'], '', block.text, 1)
                current_mcq.question_text += f" {text_to_add.strip()}"
            
            elif current_part == "option":
                option_key = self._get_analysis(block, "pattern_match", "value")
                if option_key:
                    # Remove the "(a) " part from the text
                    text_to_add = re.sub(self.config['HEURISTICS']['PATTERNS']['REGEX_OPTION'], '', block.text, 1)
                    current_mcq.options[option_key] = current_mcq.options.get(option_key, "") + f" {text_to_add.strip()}"
            
            elif current_part == "explanation":
                if pattern_type == "answer_marker" and not current_mcq.answer:
                    current_mcq.answer = self._get_analysis(block, "pattern_match", "value")
                
                # Remove the "Ans: (c) " part for the first line of explanation
                text_to_add = re.sub(self.config['HEURISTICS']['PATTERNS']['REGEX_ANSWER'], '', block.text, 1, re.IGNORECASE)
                if current_mcq.explanation is None: current_mcq.explanation = ""
                current_mcq.explanation += f" {text_to_add.strip()}"
        
        if current_mcq: # Add the last MCQ
            mcqs.append(current_mcq)
            
        # Clean up whitespace
        for mcq in mcqs:
            mcq.question_text = mcq.question_text.strip()
            if mcq.explanation: mcq.explanation = mcq.explanation.strip()
            for k, v in mcq.options.items():
                mcq.options[k] = v.strip()

        return sorted(mcqs, key=lambda m: m.question_number)
```
</code>

---
<file> main.py </file>
<code>
```python
# in main.py
import sys
from orchestrator import Orchestrator

def main():
    """
    Main entry point for the document processing script.
    Usage: python main.py [path_to_pdf]
    """
    print("--- MCQ Extraction Process Starting ---")

    # The Orchestrator loads its default config, including the default PDF path.
    # We can override it with a command-line argument.
    orchestrator = Orchestrator()

    pdf_path = orchestrator.config.get("PDF_PATH")
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        print(f"Using PDF path from command line: {pdf_path}")
    else:
        print(f"Using default PDF path from config: {pdf_path}")

    try:
        # The run method executes all phases and saves intermediate files
        final_mcqs = orchestrator.run(pdf_path)

        # You can now work with the final_mcqs list of objects
        if final_mcqs:
            print("\n--- Example of First Extracted MCQ ---")
            first_mcq = final_mcqs[0]
            print(f"Q{first_mcq.question_number}: {first_mcq.question_text}")
            for key, val in first_mcq.options.items():
                print(f"  ({key}) {val}")
            print(f"Answer: {first_mcq.answer}")
            print(f"Explanation: {first_mcq.explanation[:150]}...")
            print("------------------------------------")

    except FileNotFoundError:
        print(f"\nError: PDF file not found at '{pdf_path}'.")
        print("Please check the path in config.py or provide it as a command-line argument.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
```
</code>