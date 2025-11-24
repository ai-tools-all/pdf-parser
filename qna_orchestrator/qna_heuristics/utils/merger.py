from typing import List, Dict
from qna_orchestrator.qna_heuristics.data_models import MCQ
import logging

logger = logging.getLogger(__name__)

class ExamMerger:
    """Utility for merging question and solution MCQ lists."""
    
    @staticmethod
    def merge(questions: List[MCQ], solutions: List[MCQ]) -> List[MCQ]:
        """
        Merges solution details (answer, explanation) into the question objects.
        Matches by question_number.
        
        Args:
            questions: List of MCQ objects with question text and options
            solutions: List of MCQ objects with answers and explanations
            
        Returns:
            List of merged MCQ objects with complete data
        """
        # 1. Index solutions for O(1) lookup
        sol_map = {s.question_number: s for s in solutions}
        
        merged_results = []
        matched_count = 0
        unmatched_questions = []

        # 2. Iterate through questions and enrich
        for q in questions:
            if q.question_number in sol_map:
                sol = sol_map[q.question_number]
                
                # Enrich fields
                q.answer = sol.answer
                q.explanation = sol.explanation
                matched_count += 1
            else:
                logger.warning(f"No solution found for Question {q.question_number}")
                unmatched_questions.append(q.question_number)
            
            merged_results.append(q)

        # 3. Log stats
        logger.info(f"Merge Complete. Matched {matched_count}/{len(questions)} questions.")
        
        if unmatched_questions:
            logger.warning(f"Unmatched questions: {unmatched_questions}")
        
        # 4. Check for extra solutions (solutions without matching questions)
        question_numbers = {q.question_number for q in questions}
        extra_solutions = [s.question_number for s in solutions if s.question_number not in question_numbers]
        
        if extra_solutions:
            logger.warning(f"Solutions found without matching questions: {extra_solutions}")
        
        return merged_results
