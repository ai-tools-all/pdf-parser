# in orchestrator.py
import re 
import os
import json
from copy import deepcopy
from typing import Dict, Any, List, Optional
from qna_orchestrator.qna_heuristics.conf import load_config
from qna_orchestrator.qna_heuristics.data_models import Document, MCQ, TextBlock, Page, BaseParser
from qna_orchestrator.qna_heuristics.parser_factory import ParserFactory


class Orchestrator:
    def __init__(
        self,
        full_config: Optional[Dict] = None,
        parser: Optional[BaseParser] = None
    ):
        """
        Initialize the Orchestrator.

        Args:
            full_config: Full configuration dictionary. If not provided, uses default config.
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
        if full_config:
            self.config = deepcopy(full_config)
        else:
            self.config = load_config()
        
        # Use provided parser or create from config
        if parser:
            self.parser = parser
        else:
            self.parser = ParserFactory.create_from_config(self.config)
        
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
        Assembles MCQs using hybrid signal: Cluster Break + Question Number Pattern.
        This ensures accurate question boundaries for VisionIAS format.
        """
        mcqs = []
        all_blocks = []
        
        # Flatten blocks in reading order
        for page in doc.pages:
            all_blocks.extend(sorted(page.left_column_blocks, key=lambda b: b.bbox[1]))
            all_blocks.extend(sorted(page.right_column_blocks, key=lambda b: b.bbox[1]))

        current_mcq = None
        current_part = None
        last_option_key = None

        for i, block in enumerate(all_blocks):
            
            # --- EXTRACT ANALYSIS SIGNALS ---
            # 1. Question Start (Regex)
            q_start_res = self._get_analysis(block, "question_start", "is_question_start", default=False)
            q_num_extracted = self._get_analysis(block, "question_start", "question_number")
            
            # 2. Cluster Break (HDBSCAN)
            cluster_res = None
            for r in block.analysis_results:
                if r.get("heuristic_name") == "hdbscan_clustering":
                    cluster_res = r
                    break
            
            is_new_cluster = cluster_res.get("is_new_cluster", False) if cluster_res else False
            
            # --- DECISION LOGIC ---
            
            # It is a new question if:
            # A) It's a new cluster AND looks like a number "1." (Strongest Signal)
            # B) It's the very first block and looks like a number (Start of doc)
            is_valid_start = (is_new_cluster and q_start_res) or (current_mcq is None and q_start_res)

            if is_valid_start:
                # Save previous
                if current_mcq:
                    mcqs.append(current_mcq)
                
                # Create New
                current_mcq = MCQ(question_number=int(q_num_extracted), question_text="")
                current_part = "question"
                last_option_key = None
                
                # Remove number from text (e.g., "1. Question..." -> "Question...")
                text_to_add = re.sub(r'^\s*\d+\.\s*', '', block.text, 1)
                current_mcq.question_text = text_to_add.strip()
                continue

            if not current_mcq:
                continue

            # --- CONTENT CLASSIFICATION ---
            classification = self._get_classification(block)
            content_type = classification.get("type") if classification else "continuation"

            # Handle content
            if content_type == "option":
                current_part = "option"
                option_pattern = r'^\(?([a-d])\)?\s+'
                match = re.match(option_pattern, block.text.strip(), re.IGNORECASE)
                if match:
                    option_key = match.group(1).lower()
                    text_to_add = re.sub(option_pattern, '', block.text, 1)
                    current_mcq.options[option_key] = text_to_add.strip()
                    last_option_key = option_key
                elif last_option_key:
                    current_mcq.options[last_option_key] += f" {block.text.strip()}"
            
            else:
                # Append text to whatever part we are currently in
                text_content = block.text.strip()
                
                if current_part == "question":
                    current_mcq.question_text += f" {text_content}"
                elif current_part == "option" and last_option_key:
                    current_mcq.options[last_option_key] += f" {text_content}"
                # We ignore explanation logic for this "Questions Only" parser

        # Append last MCQ
        if current_mcq:
            mcqs.append(current_mcq)

        final_mcqs = self._merge_mcqs(mcqs)
        
        # Final cleanup of spaces
        for mcq in final_mcqs:
            mcq.question_text = ' '.join(mcq.question_text.split())
            for k, v in mcq.options.items():
                mcq.options[k] = ' '.join(v.split())
                
        return final_mcqs
