# Question + Solution Parsing Integration Plan

## Overview
Integrate Question parsing and Solution parsing into a single workflow that produces a unified JSON output with complete MCQ data.

## Strategy
Create a **High-Level Runner** script (`run_vision_pair.py`) that:
1. Initialize Orchestrator with **Question Profile**
2. Parse Question PDF
3. Re-initialize Orchestrator with **Solution Profile**
4. Parse Solution PDF
5. **Merge** the two objects in memory based on `question_number`
6. Save unified JSON

## Implementation Steps

### 1. Create `merger.py`
**File:** `qna_orchestrator/qna_heuristics/utils/merger.py`

Utility to handle merging of two lists of `MCQ` objects:
- Index solutions by `question_number` for O(1) lookup
- Iterate through questions and enrich with `answer` and `explanation`
- Log match statistics and warnings for unmatched questions

### 2. Create `run_vision_pair.py`
**File:** `run_vision_pair.py` (root directory)

Main runner script that:
- Takes `--q_pdf` and `--s_pdf` as input arguments
- Parses questions using `vision_ias_questions` profile
- Parses solutions using `vision_ias_solutions` profile
- Merges results using `ExamMerger`
- Saves output:
  - `raw_questions.json`: Questions only
  - `raw_solutions.json`: Solutions only
  - `final_exam_merged.json`: Complete merged data
  - Metadata with statistics

## Usage Example
```bash
python run_vision_pair.py \
  --q_pdf data/vision_test_4701_questions.pdf \
  --s_pdf data/vision_test_4701_solutions.pdf
```

## Output Structure
```
output/merged_exams/20251125_vision_test_4701.../
├── raw_questions.json
├── raw_solutions.json
├── final_exam_merged.json
└── metadata.json
```

### Final Merged JSON Format
```json
[
  {
    "question_number": 1,
    "question_text": "Consider the following statements...",
    "options": {"a": "...", "b": "...", "c": "...", "d": "..."},
    "answer": "c",
    "explanation": "The Citizenship Act, 1955 prescribes..."
  }
]
```

## Test Files
- Question PDF: `/home/abhishek/Downloads/chrome/search_space/prelims/2026-vision/VP_TEST-01_question_paper.pdf`
- Solution PDF: `/home/abhishek/Downloads/chrome/search_space/prelims/2026-vision/VP_TEST-01_solution.pdf`
