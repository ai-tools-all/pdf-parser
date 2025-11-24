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
from qna_orchestrator.qna_heuristics.data_models import Document, MCQ, TextBlock, AnalysisContext, Page
from qna_orchestrator.qna_heuristics.heuristics.layout import analyze_block_layout


class Orchestrator:
    def __init__(self, config_overrides: Optional[Dict] = None):
        self.config = deepcopy(get_config())
        if config_overrides:
            # A more robust implementation would merge nested dicts
            self.config.update(config_overrides)
        
        self.heuristics = self._load_heuristics()
        self.heuristics.append(analyze_block_layout)  # Add the new heuristic
        from qna_orchestrator.qna_heuristics.heuristics.question_start import is_question_start
        self.heuristics.append(is_question_start)
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
            self._analyze_scope(page.left_column_blocks, page)
            self._analyze_scope(page.right_column_blocks, page)
        return analyzed_doc

    def _analyze_scope(self, blocks: List[TextBlock], page: Page):
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

        previous_analysis = None
        for i, block in enumerate(blocks):
            prev_block = blocks[i-1] if i > 0 else None
            context = AnalysisContext(
                current_block=block,
                previous_block=prev_block,
                all_blocks_in_scope=blocks,
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

class StructureAssembler:
    def __init__(self, config):
        self.config = config
        self.last_option_key = None

    def _get_analysis(self, block: TextBlock, heuristic_name: str, key: str, default=None):
        for result in block.analysis_results:
            if result.get("heuristic_name") == heuristic_name:
                return result.get(key, default)
        return default

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

    def _get_classification(self, block: TextBlock):
        for result in block.analysis_results:
            if result.get("heuristic_name") == "content_classification":
                return result
        return None

    def assemble(self, doc: Document) -> List[MCQ]:
        """
        Assembles the final list of MCQs from the analyzed document.
        This version processes each column on each page separately to handle multi-column layouts.
        """
        mcqs = []
        
        all_blocks = []
        for page in doc.pages:
            # A basic column sequencing. A more sophisticated approach would be needed for complex layouts.
            # This assumes left column is read top-to-bottom, then right column top-to-bottom.
            all_blocks.extend(sorted(page.left_column_blocks, key=lambda b: b.bbox[1]))
            all_blocks.extend(sorted(page.right_column_blocks, key=lambda b: b.bbox[1]))

        current_mcq = None
        current_part = None
        last_option_key = None

        for i, block in enumerate(all_blocks):
            question_start_analysis = self._get_analysis(block, "question_start", "is_question_start", default=False)
            if question_start_analysis:
                if current_mcq:
                    mcqs.append(current_mcq)
                
                q_num = self._get_analysis(block, "question_start", "question_number")
                current_mcq = MCQ(question_number=q_num, question_text="")
                current_part = "question"
                last_option_key = None
                
                # Clean the question number from the text
                text_to_add = re.sub(r'^\d+\.\s*', '', block.text, 1)
                current_mcq.question_text = text_to_add.strip()
                continue

            if not current_mcq:
                continue

            classification = self._get_classification(block)
            
            # Look ahead to see if the next block is a question start
            is_next_block_question_start = False
            if i + 1 < len(all_blocks):
                next_block = all_blocks[i+1]
                if self._get_analysis(next_block, "question_start", "is_question_start", default=False):
                    is_next_block_question_start = True

            if is_next_block_question_start and current_part != "explanation":
                current_part = "explanation"

            if not classification:
                # If no classification, append to the last part
                if current_part == "question":
                    current_mcq.question_text += f" {block.text.strip()}"
                elif current_part == "option" and last_option_key:
                    current_mcq.options[last_option_key] += f" {block.text.strip()}"
                elif current_part == "explanation":
                    current_mcq.explanation += f" {block.text.strip()}"
                continue

            content_type = classification.get("type")

            if content_type == "question":
                current_part = "question"
                current_mcq.question_text += f" {block.text.strip()}"

            elif content_type == "option":
                current_part = "option"
                option_pattern = r'^\(?([abcd])\)?\s+'
                match = re.match(option_pattern, block.text.strip(), re.IGNORECASE)
                if match:
                    option_key = match.group(1).lower()
                    text_to_add = re.sub(option_pattern, '', block.text, 1)
                    current_mcq.options[option_key] = text_to_add.strip()
                    last_option_key = option_key
                elif last_option_key:
                    current_mcq.options[last_option_key] += f" {block.text.strip()}"

            elif content_type == "answer":
                current_part = "explanation"
                answer_analysis = next((r for r in block.analysis_results if r.get("heuristic_name") == "answer_boundary"), None)
                if answer_analysis:
                    current_mcq.answer = answer_analysis.get("answer")
                    current_mcq.explanation = answer_analysis.get("explanation_text", "")

            elif content_type == "explanation":
                current_part = "explanation"
                if current_mcq.explanation is None:
                    current_mcq.explanation = ""
                current_mcq.explanation += f" {block.text.strip()}"
            
            elif content_type == "continuation":
                if current_part == "question":
                    current_mcq.question_text += f" {block.text.strip()}"
                elif current_part == "option" and last_option_key:
                    current_mcq.options[last_option_key] += f" {block.text.strip()}"
                elif current_part == "explanation":
                    if current_mcq.explanation is None:
                        current_mcq.explanation = ""
                    current_mcq.explanation += f" {block.text.strip()}"


        if current_mcq:
            mcqs.append(current_mcq)

        final_mcqs = self._merge_mcqs(mcqs)
        for mcq in final_mcqs:
            mcq.question_text = ' '.join(mcq.question_text.split())
        return final_mcqs
