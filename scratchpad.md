# Scratchpad

## Task: Implement Advanced Heuristics for MCQ Extraction

**User Requirements:**
1.  Handle two-column PDF layouts.
2.  Use line spacing to identify question boundaries.
3.  Detect questions where the first line is bold.
4.  Detect questions starting with "Consider the following statements:".
5.  Identify answers starting with "Ans:" followed by an indented explanation.

**Plan:**

- [X] **1. Create Heuristic for Two-Column Layout:** Implemented a heuristic based on the provided `A004_line_spacing_wihtA003.py` to process text from two-column layouts.
- [X] **2. Create Heuristic for Line Spacing:** Implemented a heuristic to detect larger vertical gaps between text blocks, indicating a new question.
- [X] **3. Create Heuristic for Bold Text:** Implemented a heuristic to identify bold text, which often marks the beginning of a question.
- [X] **4. Create Heuristic for Question Keywords:** Implemented a heuristic to specifically find questions that start with "Consider the following statements:".
- [X] **5. Create Heuristic for Answer/Explanation:** Implemented a heuristic to parse the "Ans:" keyword and the indented explanation that follows.
- [X] **6. Update Configuration:** Added the new heuristics to `config.py`.
- [X] **7. Update Orchestrator:** Modified `orchestrator.py` to integrate and run the new heuristics.
- [ ] **8. Test and Verify:** Run the full pipeline and check the output in `03_final_mcqs.json` to ensure the new heuristics are working correctly.
