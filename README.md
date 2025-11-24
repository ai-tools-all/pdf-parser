# PDF MCQ Extractor

## Testing qna_orchestrator

Test MCQ extraction on any PDF:
```bash
uv run test-qna path/to/your/document.pdf
```

This will extract MCQs, display results, and save intermediate files to `output/`.

## Batch Processing (VisionIAS)

Process question and solution PDF pairs:

```bash
# Single prefix
python batch_vision_pair.py --dir /path/to/pdfs --prefix VP_TEST-01

# All pairs in directory
python batch_vision_pair.py --dir /path/to/pdfs --all

# Preview without processing
python batch_vision_pair.py --dir /path/to/pdfs --all --dry-run
```