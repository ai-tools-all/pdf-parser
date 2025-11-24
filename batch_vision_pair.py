#!/usr/bin/env python3
"""
Batch VisionIAS Exam Processor

Auto-detects question/solution PDF pairs from a directory and processes them.

Usage:
  # Single pair by prefix
  python batch_vision_pair.py --dir /path/to/pdfs --prefix VP_TEST-01

  # Process ALL pairs in directory
  python batch_vision_pair.py --dir /path/to/pdfs --all
"""

import argparse
import logging
import sys
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from qna_orchestrator.qna_heuristics.orchestrator import Orchestrator
from qna_orchestrator.qna_heuristics.utils.merger import ExamMerger
from qna_orchestrator.qna_heuristics.utils.output_manager import OutputManager
from qna_orchestrator.qna_heuristics.conf import load_config


def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger("BatchVisionPair")


def find_pdf_pair(directory: Path, prefix: str) -> Tuple[Optional[Path], Optional[Path]]:
    """
    Find question and solution PDFs matching the given prefix.
    
    Returns:
        Tuple of (question_pdf, solution_pdf) or (None, None) if not found
    """
    question_pdf = None
    solution_pdf = None
    
    for f in directory.glob(f"{prefix}*.pdf"):
        fname_lower = f.name.lower()
        # Skip Hindi versions and other variants
        if "hindi" in fname_lower or "darkhorse" in fname_lower:
            continue
        if "question" in fname_lower:
            question_pdf = f
        elif "solution" in fname_lower:
            solution_pdf = f
    
    return question_pdf, solution_pdf


def discover_all_prefixes(directory: Path) -> List[str]:
    """
    Discover all unique prefixes in the directory.
    
    Extracts prefix by removing _question_paper.pdf, _solution.pdf, etc.
    """
    prefixes = set()
    
    # Pattern to extract prefix (e.g., VP_TEST-01 from VP_TEST-01_question_paper.pdf)
    pattern = re.compile(r'^(.+?)_(?:question|solution)', re.IGNORECASE)
    
    for f in directory.glob("*.pdf"):
        match = pattern.match(f.name)
        if match:
            prefixes.add(match.group(1))
    
    return sorted(prefixes)


def process_pair(q_pdf: Path, s_pdf: Path, output_dir: Path, logger) -> bool:
    """
    Process a single question/solution pair.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Step 1: Parse Questions
        q_config = load_config("vision_ias_questions")
        orchestrator_q = Orchestrator(full_config=q_config)
        questions_data = orchestrator_q.run(str(q_pdf))
        logger.info(f"  Extracted {len(questions_data)} questions")

        # Step 2: Parse Solutions
        s_config = load_config("vision_ias_solutions")
        orchestrator_s = Orchestrator(full_config=s_config)
        solutions_data = orchestrator_s.run(str(s_pdf))
        logger.info(f"  Extracted {len(solutions_data)} solutions")

        # Step 3: Merge
        final_mcqs = ExamMerger.merge(questions_data, solutions_data)
        logger.info(f"  Merged {len(final_mcqs)} MCQs")

        # Step 4: Save
        out_man = OutputManager(str(output_dir), str(q_pdf), {"MODE": "BATCH_MERGED"})
        out_man.save_json(questions_data, "raw_questions.json")
        out_man.save_json(solutions_data, "raw_solutions.json")
        out_man.save_json(final_mcqs, "final_exam_merged.json")
        
        stats = {
            "questions_found": len(questions_data),
            "solutions_found": len(solutions_data),
            "merged_count": len(final_mcqs),
            "inputs": {
                "question_file": q_pdf.name,
                "solution_file": s_pdf.name
            }
        }
        out_man.save_metadata(stats)
        
        logger.info(f"  Output: {out_man.session_dir}")
        return True
        
    except Exception as e:
        logger.error(f"  Failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Batch VisionIAS Exam Processor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python batch_vision_pair.py --dir /path/to/pdfs --prefix VP_TEST-01
  python batch_vision_pair.py --dir /path/to/pdfs --all
  python batch_vision_pair.py --dir /path/to/pdfs --all --dry-run
        """
    )
    
    parser.add_argument('--dir', required=True, help="Directory containing PDF files")
    parser.add_argument('--prefix', help="Process single prefix (e.g., VP_TEST-01)")
    parser.add_argument('--all', action='store_true', help="Process all detected pairs")
    parser.add_argument('--output_dir', default="./output/merged_exams",
                        help="Output directory (default: ./output/merged_exams)")
    parser.add_argument('--dry-run', action='store_true', 
                        help="Show what would be processed without actually processing")
    
    args = parser.parse_args()
    logger = setup_logger()
    
    directory = Path(args.dir)
    if not directory.exists():
        logger.error(f"Directory not found: {directory}")
        sys.exit(1)
    
    output_dir = Path(args.output_dir)
    
    # Determine prefixes to process
    if args.prefix:
        prefixes = [args.prefix]
    elif args.all:
        prefixes = discover_all_prefixes(directory)
        logger.info(f"Discovered {len(prefixes)} prefixes: {prefixes}")
    else:
        parser.error("Either --prefix or --all must be specified")
    
    # Process each prefix
    results = {"success": [], "failed": [], "skipped": []}
    
    for prefix in prefixes:
        logger.info("")
        logger.info(f"{'='*60}")
        logger.info(f"Processing: {prefix}")
        logger.info(f"{'='*60}")
        
        q_pdf, s_pdf = find_pdf_pair(directory, prefix)
        
        if not q_pdf:
            logger.warning(f"  No question PDF found for prefix: {prefix}")
            results["skipped"].append((prefix, "no question PDF"))
            continue
        if not s_pdf:
            logger.warning(f"  No solution PDF found for prefix: {prefix}")
            results["skipped"].append((prefix, "no solution PDF"))
            continue
        
        logger.info(f"  Question: {q_pdf.name}")
        logger.info(f"  Solution: {s_pdf.name}")
        
        if args.dry_run:
            logger.info("  [DRY RUN] Would process this pair")
            results["success"].append(prefix)
            continue
        
        if process_pair(q_pdf, s_pdf, output_dir, logger):
            results["success"].append(prefix)
        else:
            results["failed"].append(prefix)
    
    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("BATCH PROCESSING COMPLETE")
    logger.info("=" * 60)
    logger.info(f"  Success: {len(results['success'])} - {results['success']}")
    if results["failed"]:
        logger.info(f"  Failed:  {len(results['failed'])} - {results['failed']}")
    if results["skipped"]:
        logger.info(f"  Skipped: {len(results['skipped'])} - {results['skipped']}")
    
    print(f"\n✅ Batch complete: {len(results['success'])} success, {len(results['failed'])} failed, {len(results['skipped'])} skipped")


if __name__ == "__main__":
    main()
