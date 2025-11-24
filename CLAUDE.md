
## Notes
- Use `uv` for Python package management
- Prefix docs with date using: `date +%Y-%m-%d-%H-%M-%S-`

## Debug Tools
Use the debug tools utility to inspect parser output and diagnose extraction issues:

```bash
# Quick stats: MCQ count, first/last questions, gap detection
python -m qna_orchestrator.qna_heuristics.utils.debug_tools --action stats \
  --mcq output/<session>/parsed_questions.json

# Inspect page blocks and reading order
python -m qna_orchestrator.qna_heuristics.utils.debug_tools --action page --target 2 \
  --json output/<session>/intermediate_analysis.json

# Find question boundary (locate Q55 start)
python -m qna_orchestrator.qna_heuristics.utils.debug_tools --action question --target 55 \
  --json output/<session>/intermediate_analysis.json

# Visualize layout detection (bounding boxes on PDF)
python -m qna_orchestrator.qna_heuristics.utils.debug_tools --action visualize \
  --pdf input.pdf --json output/<session>/intermediate_analysis.json
```

Note: Replace `<session>` with the actual session directory (e.g., `20251125_010646_extracted_pages`)
