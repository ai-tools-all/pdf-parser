# in orchestrator.py
import re 
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
        is_indented = self._get_analysis(block, "indentation", "is_indented", False)
        
        # A true question start should have a vertical break and the right pattern,
        # but it should NOT be indented. Indented numbered lists are part of the question body.
        return is_break and pattern_type == "question_start" and not is_indented

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
        print("\n--- Assembling MCQs with Detailed Logging ---")

        for block in all_blocks:
            if self._is_question_start(block):
                if current_mcq:
                    print(f"--- Finalizing MCQ {current_mcq.question_number} ---")
                    mcqs.append(current_mcq)
                
                q_num = self._get_analysis(block, "pattern_match", "value")
                current_mcq = MCQ(question_number=q_num, question_text="")
                current_part = "question"
                print(f"\n[NEW MCQ] Started MCQ #{q_num} from block '{block.id}': '{block.text.strip()}'")

            if not current_mcq:
                continue

            # State machine logic
            pattern_type = self._get_analysis(block, "pattern_match", "type")
            
            prev_part = current_part
            if current_part == "question" and pattern_type == "option":
                current_part = "option"
            elif (current_part == "question" or current_part == "option") and pattern_type == "answer_marker":
                current_part = "explanation"

            if prev_part != current_part:
                print(f"  [STATE]  Transition: {prev_part} -> {current_part} (block: {block.id}, text: '{block.text.strip()}')")

            # Append text based on current state
            if current_part == "question":
                text_to_add = re.sub(self.config['HEURISTICS']['PATTERNS']['REGEX_QUESTION'], '', block.text, 1)
                current_mcq.question_text += f" {text_to_add.strip()}"
                print(f"  [Q]      Appending: '{text_to_add.strip()}'")
            
            elif current_part == "option":
                option_key = self._get_analysis(block, "pattern_match", "value")
                if option_key:
                    text_to_add = re.sub(self.config['HEURISTICS']['PATTERNS']['REGEX_OPTION'], '', block.text, 1)
                    current_mcq.options[option_key] = current_mcq.options.get(option_key, "") + f" {text_to_add.strip()}"
                    print(f"  [Opt {option_key}] Appending: '{text_to_add.strip()}'")
                # NOTE: This logic doesn't handle option text that spans multiple blocks without a key.

            elif current_part == "explanation":
                if pattern_type == "answer_marker" and not current_mcq.answer:
                    current_mcq.answer = self._get_analysis(block, "pattern_match", "value")
                    print(f"  [Answer] Found: {current_mcq.answer}")
                
                text_to_add = re.sub(self.config['HEURISTICS']['PATTERNS']['REGEX_ANSWER'], '', block.text, 1, re.IGNORECASE)
                if current_mcq.explanation is None: current_mcq.explanation = ""
                current_mcq.explanation += f" {text_to_add.strip()}"
                print(f"  [Expl]   Appending: '{text_to_add.strip()}'")
        
        if current_mcq: # Add the last MCQ
            print(f"--- Finalizing Last MCQ {current_mcq.question_number} ---")
            mcqs.append(current_mcq)
            
        # Clean up whitespace
        for mcq in mcqs:
            mcq.question_text = mcq.question_text.strip()
            if mcq.explanation: mcq.explanation = mcq.explanation.strip()
            for k, v in mcq.options.items():
                mcq.options[k] = v.strip()

        return sorted(mcqs, key=lambda m: m.question_number)