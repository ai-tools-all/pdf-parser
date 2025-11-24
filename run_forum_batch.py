import argparse
import logging
import re
import sys
from pathlib import Path
from typing import Dict
from collections import defaultdict

from qna_orchestrator.qna_heuristics.orchestrator import Orchestrator
from qna_orchestrator.qna_heuristics.utils.merger import ExamMerger
from qna_orchestrator.qna_heuristics.utils.output_manager import OutputManager
from qna_orchestrator.qna_heuristics.conf import load_config

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ForumBatch")


class FilePairer:
    """Helper to pair Question and Solution PDFs based on Test Code."""

    def __init__(self, directory: Path, id_pattern: str = r'Test[\s\-_]?(\d+)',
                 qp_keyword: str = 'qp', sol_keyword: str = 'sol'):
        self.directory = directory
        # Regex to extract test number from patterns like "Test-2", "Test 01", etc.
        self.id_pattern = re.compile(id_pattern, re.IGNORECASE)
        self.qp_keyword = qp_keyword.lower()
        self.sol_keyword = sol_keyword.lower()

    def _get_test_id(self, filename: str) -> str:
        match = self.id_pattern.search(filename)
        return match.group(1) if match else None

    def _is_solution(self, filename: str) -> bool:
        """Heuristic to detect if file is a solution."""
        fname = filename.lower()
        return self.sol_keyword in fname

    def _is_question(self, filename: str) -> bool:
        """Heuristic to detect if file is a question paper."""
        fname = filename.lower()
        return self.qp_keyword in fname

    def find_pairs(self) -> Dict[str, Dict[str, Path]]:
        pairs = defaultdict(dict)
        files = list(self.directory.glob("*.pdf"))

        logger.info(f"Scanning {len(files)} PDFs in {self.directory}...")

        for file_path in files:
            test_id = self._get_test_id(file_path.name)

            if not test_id:
                logger.warning(f"Skipping (No Test ID found): {file_path.name}")
                continue

            # Determine role based on keywords
            if self._is_solution(file_path.name):
                role = 's'
            elif self._is_question(file_path.name):
                role = 'q'
            else:
                logger.warning(f"Skipping (Unknown role - no 'QP' or 'solution'): {file_path.name}")
                continue

            # Check for duplicates
            if role in pairs[test_id]:
                logger.warning(
                    f"Duplicate {role.upper()} found for ID {test_id}: {file_path.name}. "
                    f"Keeping {pairs[test_id][role].name}"
                )
                continue

            pairs[test_id][role] = file_path

        # Filter complete pairs
        complete_pairs = {k: v for k, v in pairs.items() if 'q' in v and 's' in v}
        logger.info(f"Found {len(complete_pairs)} complete pairs out of {len(pairs)} potential groups.")

        return complete_pairs


def process_pair(test_id: str, q_path: str, s_path: str, output_base: str):
    """Runs the extraction pipeline for a single pair."""
    logger.info(f"--- Processing Test ID: {test_id} ---")

    try:
        # 1. Parse Questions
        logger.info(f"Parsing Question: {Path(q_path).name}")
        q_config = load_config("forum_ias")
        if not q_config.get("HEURISTICS"):
            logger.error("Failed to load forum_ias profile!")
            return False

        orch_q = Orchestrator(full_config=q_config)
        questions = orch_q.run(q_path)

        # 2. Parse Solutions
        logger.info(f"Parsing Solution: {Path(s_path).name}")
        s_config = load_config("forum_ias_solutions")
        orch_s = Orchestrator(full_config=s_config)
        solutions = orch_s.run(s_path)

        # 3. Merge
        logger.info("Merging Data...")
        final_mcqs = ExamMerger.merge(questions, solutions)

        # 4. Save
        out_man = OutputManager(output_base, q_path, {"MODE": "BATCH_FORUM", "TEST_ID": test_id})

        out_man.save_json(questions, "raw_questions.json")
        out_man.save_json(solutions, "raw_solutions.json")
        out_man.save_json(final_mcqs, f"forum_{test_id}_merged.json")

        # Stats
        stats = {
            "test_id": test_id,
            "q_count": len(questions),
            "s_count": len(solutions),
            "merged_count": len(final_mcqs)
        }
        out_man.save_metadata(stats)
        logger.info(f"Success: {test_id} (Merged {len(final_mcqs)} MCQs)")
        return True

    except Exception as e:
        logger.error(f"Failed processing {test_id}: {e}", exc_info=True)
        return False


def main():
    parser = argparse.ArgumentParser(description="ForumIAS Batch Processor")
    parser.add_argument('--dir', required=True, help="Directory containing PDFs")
    parser.add_argument('--output', default="./output/forum_batch", help="Output directory")
    parser.add_argument('--id-pattern', default=r'Test[\s\-_]?(\d+)',
                        help="Regex pattern to extract test ID (default: r'Test[\\s\\-_]?(\\d+)')")
    parser.add_argument('--qp-keyword', default='qp',
                        help="Keyword to identify question papers (default: 'qp')")
    parser.add_argument('--sol-keyword', default='sol',
                        help="Keyword to identify solutions (default: 'sol')")

    args = parser.parse_args()

    input_dir = Path(args.dir)
    if not input_dir.exists():
        logger.error(f"Input directory not found: {input_dir}")
        return

    # Find pairs
    pairer = FilePairer(input_dir, args.id_pattern, args.qp_keyword, args.sol_keyword)
    pairs = pairer.find_pairs()

    if not pairs:
        logger.warning("No complete Question-Solution pairs found.")
        return

    # Process
    success_count = 0
    total = len(pairs)

    for i, (test_id, files) in enumerate(pairs.items(), 1):
        print(f"\n[{i}/{total}] Starting Batch Job for ID {test_id}")
        if process_pair(test_id, str(files['q']), str(files['s']), args.output):
            success_count += 1

    print(f"\n=== Batch Complete ===")
    print(f"Total processed: {total}")
    print(f"Successful: {success_count}")
    print(f"Failed: {total - success_count}")


if __name__ == "__main__":
    main()
