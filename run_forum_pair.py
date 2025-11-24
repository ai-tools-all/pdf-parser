#!/usr/bin/env python3
"""
ForumIAS Full Exam Processor (Questions + Solutions)

This script processes a complete exam by:
1. Parsing the Question Paper PDF
2. Parsing the Solution/Explanation PDF
3. Merging the results based on question_number
4. Saving unified JSON output
"""

import argparse
import logging
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from qna_orchestrator.qna_heuristics.orchestrator import Orchestrator
from qna_orchestrator.qna_heuristics.utils.merger import ExamMerger
from qna_orchestrator.qna_heuristics.utils.output_manager import OutputManager
from qna_orchestrator.qna_heuristics.conf import load_config


def setup_logger():
    """Configure basic logging for the runner script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def main():
    parser = argparse.ArgumentParser(
        description="ForumIAS Full Exam Processor (Questions + Solutions)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_forum_pair.py --q_pdf questions.pdf --s_pdf solutions.pdf
  python run_forum_pair.py --q_pdf q.pdf --s_pdf s.pdf --output_dir ./results
        """
    )
    
    parser.add_argument('--q_pdf', required=True, help="Path to Question Paper PDF")
    parser.add_argument('--s_pdf', required=True, help="Path to Solution/Explanation PDF")
    parser.add_argument('--output_dir', default="./output/merged_forum", 
                        help="Directory for final output (default: ./output/merged_forum)")
    
    args = parser.parse_args()
    setup_logger()
    logger = logging.getLogger("ForumPairRunner")

    # Validate input files exist
    if not os.path.exists(args.q_pdf):
        logger.error(f"Question PDF not found: {args.q_pdf}")
        sys.exit(1)
    if not os.path.exists(args.s_pdf):
        logger.error(f"Solution PDF not found: {args.s_pdf}")
        sys.exit(1)

    # --- Step 1: Parse Questions ---
    logger.info("=" * 60)
    logger.info(">>> STEP 1: Parsing Questions...")
    logger.info("=" * 60)
    
    q_config = load_config("forum_ias")
    orchestrator_q = Orchestrator(full_config=q_config)
    questions_data = orchestrator_q.run(args.q_pdf)
    logger.info(f"Extracted {len(questions_data)} questions.")

    # --- Step 2: Parse Solutions ---
    logger.info("")
    logger.info("=" * 60)
    logger.info(">>> STEP 2: Parsing Solutions...")
    logger.info("=" * 60)
    
    s_config = load_config("forum_ias_solutions")
    orchestrator_s = Orchestrator(full_config=s_config)
    solutions_data = orchestrator_s.run(args.s_pdf)
    logger.info(f"Extracted {len(solutions_data)} solutions.")

    # --- Step 3: Merge ---
    logger.info("")
    logger.info("=" * 60)
    logger.info(">>> STEP 3: Merging Data...")
    logger.info("=" * 60)
    
    final_mcqs = ExamMerger.merge(questions_data, solutions_data)
    logger.info(f"Merge complete. {len(final_mcqs)} total questions.")

    # --- Step 4: Save Final Output ---
    logger.info("")
    logger.info("=" * 60)
    logger.info(">>> STEP 4: Saving Final Output...")
    logger.info("=" * 60)
    
    out_man = OutputManager(args.output_dir, args.q_pdf, {"MODE": "MERGED_FORUM"})
    
    out_man.save_json(questions_data, "raw_questions.json")
    out_man.save_json(solutions_data, "raw_solutions.json")
    out_man.save_json(final_mcqs, "final_exam_merged.json")
    
    stats = {
        "questions_found": len(questions_data),
        "solutions_found": len(solutions_data),
        "merged_count": len(final_mcqs),
        "inputs": {
            "question_file": str(Path(args.q_pdf).name),
            "solution_file": str(Path(args.s_pdf).name)
        }
    }
    out_man.save_metadata(stats)
    
    # --- Success Summary ---
    logger.info("")
    logger.info("=" * 60)
    logger.info("SUCCESS!")
    logger.info("=" * 60)
    logger.info(f"Output directory: {out_man.session_dir}")
    logger.info(f"Files created:")
    logger.info(f"  - raw_questions.json ({len(questions_data)} questions)")
    logger.info(f"  - raw_solutions.json ({len(solutions_data)} solutions)")
    logger.info(f"  - final_exam_merged.json ({len(final_mcqs)} merged MCQs)")
    logger.info(f"  - metadata.json")
    logger.info(f"  - parser.log")
    logger.info("=" * 60)
    
    print(f"\nSUCCESS! Output saved to: {out_man.session_dir}")


if __name__ == "__main__":
    main()
