# in orchestrator.py
import re 
import os
import json
import importlib
import statistics
from copy import deepcopy
from typing import Dict, Any, List, Optional
from qna_orchestrator.qna_heuristics.config import get_config
from qna_orchestrator.qna_heuristics.pdf_parser import PDFParser
from qna_orchestrator.qna_heuristics.data_models import Document, MCQ, TextBlock, AnalysisContext

class Orchestrator:
    def __init__(self, config_overrides: Optional[Dict] = None):
        self.config = deepcopy(get_config())
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
        
        # Calculate median font size for enhanced font detection
        font_sizes = [b.font_size for b in blocks if b.font_size > 0]
        median_font_size = statistics.median(font_sizes) if font_sizes else 12.0

        for i, block in enumerate(blocks):
            prev_block = blocks[i-1] if i > 0 else None
            context = AnalysisContext(
                current_block=block,
                previous_block=prev_block,
                all_blocks_in_scope=blocks,
                scope_median_spacing=median_spacing,
                scope_min_x=min_x,
                scope_median_font_size=median_font_size,
                config=self.config
            )
            for heuristic_func in self.heuristics:
                result = heuristic_func(context)
                if result:
                    block.analysis_results.append(result)

class StructureAssembler:
    def __init__(self, config):
        self.config = config
        self.last_option_key = None

    def _get_analysis(self, block: TextBlock, heuristic_name: str, key: str, default=None):
        for result in block.analysis_results:
            if result.get("heuristic_name") == heuristic_name:
                return result.get(key, default)
        return default

    def _is_question_start(self, block: TextBlock, current_mcq: Optional[MCQ]) -> bool:
        """
        Enhanced multi-signal question detection combining:
        1. Vertical spacing breaks
        2. Pattern matching (numbered + descriptive)
        3. Font styling (bold/large)
        4. Indentation rules
        """
        # Get analysis results
        is_break = self._get_analysis(block, "vertical_break", "is_break", False)
        break_type = self._get_analysis(block, "vertical_break", "break_type", "none")
        pattern_type = self._get_analysis(block, "pattern_match", "type")
        is_indented = self._get_analysis(block, "indentation", "is_indented", False)
        is_bold = self._get_analysis(block, "font_style", "is_bold", False) 
        font_question_indicator = self._get_analysis(block, "font_style", "question_indicator", False)
        
        # Signal 1: Traditional numbered questions (high confidence)
        if pattern_type == "question_start" and is_break and not is_indented:
            q_num = self._get_analysis(block, "pattern_match", "value")
            if current_mcq and q_num == current_mcq.question_number:
                return False
            return True
        
        # Signal 2: Descriptive question starts (medium confidence)
        if pattern_type == "descriptive_question_start":
            # Require either significant spacing or bold formatting
            if (break_type in ["medium_break", "large_break"] or 
                (is_bold and break_type == "small_break") or
                font_question_indicator):
                return True
        
        # Signal 3: Bold text with significant spacing (medium confidence)
        if (is_bold and break_type in ["medium_break", "large_break"] and 
            not is_indented and pattern_type != "option"):
            # Additional check: avoid false positives for emphasized text within questions
            text = block.text.strip().lower()
            if not any(word in text for word in ["statement", "option", "choice"]):
                return True
        
        # Signal 4: Large spacing with question-like content (low confidence)
        if (break_type == "large_break" and not is_indented and 
            pattern_type != "option" and pattern_type != "answer_marker"):
            text = block.text.strip()
            # Check if text looks like a question (ends with ?, contains question words)
            if (text.endswith('?') or 
                any(word in text.lower() for word in ['which', 'what', 'how', 'consider', 'identify'])):
                return True
        
        return False

    def _merge_mcqs(self, mcqs: List[MCQ]) -> List[MCQ]:
        merged_mcqs_dict = {}
        for mcq in mcqs:
            q_num = mcq.question_number
            if q_num not in merged_mcqs_dict:
                merged_mcqs_dict[q_num] = mcq
            else:
                existing_mcq = merged_mcqs_dict[q_num]
                if mcq.question_text:
                    existing_mcq.question_text += f" {mcq.question_text.strip()}"
                existing_mcq.options.update(mcq.options)
                if mcq.answer:
                    existing_mcq.answer = mcq.answer
                if mcq.explanation:
                    if existing_mcq.explanation:
                        existing_mcq.explanation += f" {mcq.explanation.strip()}"
                    else:
                        existing_mcq.explanation = mcq.explanation.strip()
        return list(merged_mcqs_dict.values())

    def assemble(self, doc: Document) -> List[MCQ]:
        """
        Assembles the final list of MCQs from the analyzed document.
        This version processes each column on each page separately to handle multi-column layouts.
        """
        mcqs = []

        # Process blocks page by page, column by column
        for page in doc.pages:
            for column_blocks in [page.left_column_blocks, page.right_column_blocks]:
                if not column_blocks:
                    continue

                # State machine for each column
                current_mcq = None
                current_part = "question"
                self.last_option_key = None

                for block in column_blocks:
                    if self._is_question_start(block, current_mcq):
                        if current_mcq:
                            mcqs.append(current_mcq)
                        
                        q_num = self._get_analysis(block, "pattern_match", "value")
                        current_mcq = MCQ(question_number=q_num, question_text="")
                        current_part = "question"
                        self.last_option_key = None
                        
                        # Clean the question number from the text
                        text_to_add = re.sub(self.config['HEURISTICS']['PATTERNS']['REGEX_QUESTION'], '', block.text, 1)
                        current_mcq.question_text = text_to_add.strip()
                        continue

                    if not current_mcq:
                        continue

                    # --- State transition logic ---
                    pattern_type = self._get_analysis(block, "pattern_match", "type")
                    if pattern_type == "option" and current_part != "explanation":
                        current_part = "option"
                    elif pattern_type == "answer_marker":
                        current_part = "explanation"
                        self.last_option_key = None

                    # --- Content assembly logic ---
                    if current_part == "question":
                        # If there's a significant vertical break, we assume the question text has ended.
                        if self._get_analysis(block, "vertical_break", "value"):
                            current_part = "seek_option" # State indicating we're done with question text.

                        # Append text only if we are still in the question part and it's not a recognized component.
                        if current_part == "question" and not pattern_type:
                            current_mcq.question_text += f" {block.text.strip()}"

                    elif current_part == "option":
                        option_key = self._get_analysis(block, "pattern_match", "value")
                        if option_key:
                            text_to_add = re.sub(self.config['HEURISTICS']['PATTERNS']['REGEX_OPTION'], '', block.text, 1)
                            current_mcq.options[option_key] = text_to_add.strip()
                            self.last_option_key = option_key
                        elif self.last_option_key:
                            # Append to the last seen option (for multi-line options)
                            current_mcq.options[self.last_option_key] += f" {block.text.strip()}"

                    elif current_part == "explanation":
                        if pattern_type == "answer_marker" and not current_mcq.answer:
                            current_mcq.answer = self._get_analysis(block, "pattern_match", "value")
                        
                        # Clean the 'Ans:' part from the text
                        text_to_add = re.sub(self.config['HEURISTICS']['PATTERNS']['REGEX_ANSWER'], '', block.text, 1, re.IGNORECASE)
                        
                        if current_mcq.explanation is None:
                            current_mcq.explanation = text_to_add.strip()
                        else:
                            current_mcq.explanation += f" {text_to_add.strip()}"

                # Add the last MCQ from the column if it exists
                if current_mcq:
                    mcqs.append(current_mcq)

        # Merge and clean up the final list
        final_mcqs = self._merge_mcqs(mcqs)
        for mcq in final_mcqs:
            # Final cleanup of question text
            mcq.question_text = ' '.join(mcq.question_text.split())
        return final_mcqs