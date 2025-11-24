# in orchestrator.py
import re 
import os
import json
import logging
from copy import deepcopy
from typing import Dict, Any, List, Optional
from qna_orchestrator.qna_heuristics.conf import load_config
from qna_orchestrator.qna_heuristics.data_models import Document, MCQ, TextBlock, Page, BaseParser
from qna_orchestrator.qna_heuristics.parser_factory import ParserFactory
from qna_orchestrator.qna_heuristics.utils.output_manager import OutputManager


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
        
        # OutputManager is initialized in run() because we need pdf_path
        self.output_manager = None



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
        # Initialize Output Manager
        self.output_manager = OutputManager(
            self.config["OUTPUT_DIR"], 
            pdf_path, 
            self.config
        )
        logger = self.output_manager.logger

        try:
            # --- Phase 1: Parse PDF (extraction + layout + analysis) ---
            logger.info(f"Starting parsing for: {pdf_path}")
            doc = self.parser.parse(pdf_path)
            
            if self.config.get("SAVE_INTERMEDIATE_JSON"):
                self.output_manager.save_json(doc, "intermediate_analysis.json")
            
            # --- Phase 2: Assemble MCQs ---
            logger.info("Assembling MCQs...")
            
            # Pass logger to Assembler
            assembler = StructureAssembler(self.config, logger)
            mcqs = assembler.assemble(doc)
            
            # --- Output ---
            self.output_manager.save_json(mcqs, "parsed_questions.json")
            
            # Save Metadata
            stats = {
                "total_questions": len(mcqs),
                "total_pages": len(doc.pages)
            }
            self.output_manager.save_metadata(stats)
            
            logger.info(f"Completed. Extracted {len(mcqs)} MCQs.")
            return mcqs

        except Exception as e:
            logger.error(f"Orchestrator Failed: {e}", exc_info=True)
            raise

class StructureAssembler:
    def __init__(self, config, logger=None):
        self.config = config
        self.logger = logger or logging.getLogger("Dummy")
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
        Dispatcher method that selects the right assembly strategy based on config.
        """
        strategy = self.config.get("ASSEMBLY_STRATEGY", "default")
        
        if strategy == "vision_gatekeeper":
            self.logger.info("Using Assembly Strategy: Vision Gatekeeper (Option d Sequential)")
            return self._assemble_vision_gatekeeper(doc)
        elif strategy == "vision_solutions":
            self.logger.info("Using Assembly Strategy: Vision Solutions (Header-Based Extraction)")
            return self._assemble_vision_solutions(doc)
        else:
            self.logger.info("Using Assembly Strategy: Default Sequential")
            return self._assemble_default(doc)

    def _assemble_vision_gatekeeper(self, doc: Document) -> List[MCQ]:
        """
        Vision IAS Gatekeeper Strategy:
        Uses Option (d) as the "gate" to determine when a new question can start.
        
        Logic:
        - Gate starts UNLOCKED (to find Q1)
        - When we find a valid question number, LOCK the gate
        - Numbers found while LOCKED are treated as content (e.g., numbered statements)
        - When we see option (d), UNLOCK the gate
        - Next valid number with UNLOCKED gate starts new question
        
        This prevents false positives from numbered statements inside questions.
        """
        mcqs = []
        all_blocks = []
        
        # 1. Flatten blocks in reading order
        #    For Vision IAS: process other_blocks by assigning to appropriate column
        for page in doc.pages:
            # Calculate page midpoint to determine left vs right column
            page_mid_x = page.page_width / 2 if page.page_width else 300
            
            # Assign other_blocks to appropriate columns based on X position
            left_blocks = list(page.left_column_blocks)
            right_blocks = list(page.right_column_blocks)
            
            for block in page.other_blocks:
                block_center_x = (block.bbox[0] + block.bbox[2]) / 2
                if block_center_x < page_mid_x:
                    left_blocks.append(block)
                else:
                    right_blocks.append(block)
            
            # Sort each column by Y position (top to bottom)
            left = sorted(left_blocks, key=lambda b: b.bbox[1])
            right = sorted(right_blocks, key=lambda b: b.bbox[1])
            
            # Reading order: left column first, then right column
            all_blocks.extend(left + right)

        # 2. State Machine Variables
        current_mcq = None
        current_part = "question"  # 'question' or 'option'
        last_option_key = None
        
        expected_q_num = 1
        gate_unlocked = True  # Initially unlocked to find Q1
        
        # Get regex from config (allows profile-specific tweaks)
        patterns = self.config.get("HEURISTICS", {}).get("PATTERNS", {})
        q_regex = patterns.get("REGEX_QUESTION", r'^\s*(\d{1,3})\.')
        opt_regex = patterns.get("REGEX_OPTION", r'^\s*\(([a-d])\)')
        
        q_num_pattern = re.compile(q_regex)
        option_pattern = re.compile(opt_regex, re.IGNORECASE)

        for block in all_blocks:
            text = block.text.strip()
            if not text:
                continue

            # --- CHECK FOR QUESTION START ---
            q_match = q_num_pattern.match(text)
            is_new_question = False
            
            if q_match:
                found_num = int(q_match.group(1))
                
                # CRITICAL LOGIC: Only accept as new question if gate is unlocked
                if found_num == expected_q_num and gate_unlocked:
                    is_new_question = True

            # --- PROCESS NEW QUESTION ---
            if is_new_question:
                # Save previous MCQ
                if current_mcq:
                    mcqs.append(current_mcq)
                
                # Start new MCQ
                current_mcq = MCQ(question_number=found_num, question_text="")
                current_part = "question"
                last_option_key = None
                
                # Clean text (remove "1." prefix)
                clean_text = q_num_pattern.sub('', text, count=1).strip()
                if clean_text:
                    current_mcq.question_text = clean_text
                
                # Update state
                expected_q_num += 1
                gate_unlocked = False  # LOCK THE GATE until we see (d)
                continue

            # Skip blocks until we find Q1
            if not current_mcq:
                continue

            # --- PROCESS OPTIONS & CONTENT ---
            opt_match = option_pattern.match(text)
            
            if opt_match:
                # Found an option (a), (b), (c), or (d)
                opt_key = opt_match.group(1).lower()
                current_part = "option"
                last_option_key = opt_key
                
                # Extract text after "(a)"
                clean_text = option_pattern.sub('', text, count=1).strip()
                current_mcq.options[opt_key] = clean_text

                # UNLOCK GATE when we see option (d)
                if opt_key == 'd':
                    gate_unlocked = True

            else:
                # Continuation text
                if current_part == "question":
                    current_mcq.question_text += " " + text
                elif current_part == "option" and last_option_key:
                    current_mcq.options[last_option_key] += " " + text

        # Save last MCQ
        if current_mcq:
            mcqs.append(current_mcq)

        return self._post_process_mcqs(mcqs)

    def _assemble_default(self, doc: Document) -> List[MCQ]:
        """
        Default Sequential State Machine approach.
        Tracks expected question number and advances on strict sequence match.
        """
        mcqs = []
        
        # 1. Flatten all blocks in strictly sorted order
        all_blocks = []
        for page in doc.pages:
            left = sorted(page.left_column_blocks, key=lambda b: b.bbox[1])
            right = sorted(page.right_column_blocks, key=lambda b: b.bbox[1])
            all_blocks.extend(left + right)

        # 2. Initialize State Machine
        current_mcq = None
        current_part = None      # 'question', 'option'
        last_option_key = None
        
        expected_q_num = 1       # We start looking for Q1
        
        # Regex for finding "1." "2." etc.
        q_num_pattern = re.compile(r'^\s*(\d{1,3})\.') 

        for block in all_blocks:
            text = block.text.strip()
            
            # --- CHECK FOR QUESTION START ---
            match = q_num_pattern.match(text)
            is_question_start = False
            found_num = -1

            if match:
                found_num = int(match.group(1))
                
                # LOGIC: Is this the number we are looking for?
                if found_num == expected_q_num:
                    is_question_start = True
                
                # GAP RECOVERY: Did we miss one? (e.g. looking for 6, found 7)
                elif found_num == expected_q_num + 1:
                    self.logger.warning(f"Missed Question {expected_q_num}, jumping to {found_num}")
                    expected_q_num = found_num # Sync up
                    is_question_start = True
            
            # --- PROCESS BLOCK ---
            
            if is_question_start:
                # Save previous
                if current_mcq:
                    mcqs.append(current_mcq)
                
                # Start New
                current_mcq = MCQ(question_number=found_num, question_text="")
                current_part = "question"
                last_option_key = None
                expected_q_num += 1
                
                # Remove the number "55." from the text
                cleaned_text = q_num_pattern.sub('', text).strip()
                
                if cleaned_text:
                    current_mcq.question_text = cleaned_text
                continue

            # If we haven't found Q1 yet, skip everything
            if not current_mcq:
                continue

            # --- CONTENT PARSING (for current MCQ) ---
            
            # Check for Options (a), (b)...
            option_match = re.match(r'^\(?([a-d])\)?\s+', text, re.IGNORECASE)
            
            if option_match:
                current_part = "option"
                option_key = option_match.group(1).lower()
                cleaned_text = re.sub(r'^\(?([a-d])\)?\s+', '', text, count=1, flags=re.IGNORECASE).strip()
                
                current_mcq.options[option_key] = cleaned_text
                last_option_key = option_key
            
            else:
                # Continuation of whatever we were doing
                if current_part == "question":
                    current_mcq.question_text += f" {text}"
                elif current_part == "option" and last_option_key:
                    current_mcq.options[last_option_key] += f" {text}"

        # Save the last one
        if current_mcq:
            mcqs.append(current_mcq)

        return self._post_process_mcqs(mcqs)

    def _assemble_vision_solutions(self, doc: Document) -> List[MCQ]:
        """
        Vision IAS Solutions Strategy:
        Treats "Q X.Y" as hard splitter where X is question number and Y is correct answer.
        Everything following that header (until next header) is the Explanation.
        
        Example: "Q 1.C The Citizenship Act..." -> Q#1, Answer: c, Explanation: "The Citizenship Act..."
        """
        mcqs = []
        all_blocks = []
        
        # Flatten blocks (Reading Order: top-to-bottom, left-to-right)
        for page in doc.pages:
            # Vision Solutions usually run single column or flow naturally
            # We strictly sort top-to-bottom, left-to-right
            page_blocks = page.left_column_blocks + page.right_column_blocks + page.other_blocks
            all_blocks.extend(sorted(page_blocks, key=lambda b: (b.bbox[1], b.bbox[0])))

        current_mcq = None
        
        # Regex: Q [Num].[Option]
        # e.g. "Q 1.C" -> Num=1, Ans=C
        header_regex = self.config.get("HEURISTICS", {}).get("PATTERNS", {}).get("REGEX_SOLUTION_HEADER")
        if not header_regex:
            self.logger.error("REGEX_SOLUTION_HEADER not found in config")
            return []
        
        header_pattern = re.compile(header_regex, re.IGNORECASE)

        for block in all_blocks:
            text = block.text.strip()
            if not text:
                continue

            match = header_pattern.match(text)
            
            if match:
                # Found "Q 1.C"
                if current_mcq:
                    mcqs.append(current_mcq)
                
                q_num = int(match.group(1))
                correct_ans = match.group(2).lower()  # 'c'
                
                # Start new MCQ object (Question text blank, Options blank)
                current_mcq = MCQ(
                    question_number=q_num,
                    question_text="",
                    answer=correct_ans,
                    explanation=""
                )
                
                # If there is text *after* "Q 1.C" in the same block, add it to explanation
                # e.g., "Q 1.C The Citizenship Act..."
                remaining_text = header_pattern.sub('', text).strip()
                if remaining_text:
                    current_mcq.explanation = remaining_text

            elif current_mcq:
                # It's part of the explanation
                current_mcq.explanation += f" {text}"

        # Save last MCQ
        if current_mcq:
            mcqs.append(current_mcq)

        return self._post_process_solutions(mcqs)

    def _post_process_solutions(self, mcqs):
        """Helper to clean up extra spaces in solutions"""
        for mcq in mcqs:
            if mcq.explanation:
                # Cleanup spaces
                mcq.explanation = ' '.join(mcq.explanation.split())
        return mcqs

    def _post_process_mcqs(self, mcqs):
        """Helper to clean up extra spaces"""
        for mcq in mcqs:
            mcq.question_text = ' '.join(mcq.question_text.split())
            for k, v in mcq.options.items():
                mcq.options[k] = ' '.join(v.split())
        return mcqs
