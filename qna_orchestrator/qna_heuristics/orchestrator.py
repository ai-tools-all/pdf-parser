# in orchestrator.py
import re 
import os
import json
from copy import deepcopy
from typing import Dict, Any, List, Optional
from qna_orchestrator.qna_heuristics.config import get_config
from qna_orchestrator.qna_heuristics.data_models import Document, MCQ, TextBlock, Page, BaseParser
from qna_orchestrator.qna_heuristics.parser_factory import ParserFactory


class Orchestrator:
    def __init__(
        self,
        config_overrides: Optional[Dict] = None,
        parser: Optional[BaseParser] = None
    ):
        """
        Initialize the Orchestrator.
        
        Args:
            config_overrides: Optional config overrides
            parser: Optional custom parser. If not provided, uses default parser.
        
        Example:
            # Use default parser
            orchestrator = Orchestrator()
            
            # Use custom parser
            custom_parser = ParserFactory.create_custom(
                extraction=MyExtractor(config),
                layout=MyLayout(config),
                analysis=MyAnalyzer(config),
                config=config
            )
            orchestrator = Orchestrator(parser=custom_parser)
        """
        self.config = deepcopy(get_config())
        if config_overrides:
            # A more robust implementation would merge nested dicts
            self.config.update(config_overrides)
        
        # Use provided parser or create default
        if parser:
            self.parser = parser
        else:
            self.parser = ParserFactory.create_default(self.config)
        
        os.makedirs(self.config["OUTPUT_DIR"], exist_ok=True)

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
        """
        Run the complete MCQ extraction pipeline.
        
        Pipeline:
        1. Parse PDF (extract + layout + analyze) - done by parser
        2. Assemble MCQs from analyzed document
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of extracted MCQ objects
        """
        # --- Phase 1: Parse PDF (extraction + layout + analysis) ---
        print("Phase 1: Parsing and analyzing PDF...")
        doc = self.parser.parse(pdf_path)
        self._save_json(doc, "01_analyzed_document.json")
        
        # --- Phase 2: Assemble MCQs ---
        print("Phase 2: Assembling MCQs...")
        assembler = StructureAssembler(self.config)
        mcqs = assembler.assemble(doc)
        self._save_json(mcqs, "02_final_mcqs.json")

        print(f"\nExtraction complete. Found {len(mcqs)} MCQs.")
        return mcqs

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
