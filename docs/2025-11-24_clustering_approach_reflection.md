# Reflection: Clustering Approach for VisionIAS MCQ Parsing
**Date**: 2025-11-24

## Objective
Implement a clustering-based approach using HDBSCAN to accurately detect question boundaries in VisionIAS PDF format, which has:
- Numbered questions (1., 2., 3., etc.)
- No explicit visual separators between questions
- Watermarks and noise text scattered throughout (`@iasvault`, `Dark horse`, `www.visionias.in`)
- Two-column layout
- Instructions page that should be skipped

## Approach Taken

### 1. Noise Filtering at Extraction Phase
**Implementation**: Added `NOISE_PATTERNS` config and filtered text during extraction in both `PyMuPDFExtractor` and `PDFParser`.

**Patterns filtered**:
- `www.visionias.in`, `©Vision IAS`, `@iasvault`, `Dark horse`
- Instruction text: `IMMEDIATELY AFTER THE COMMENCEMENT`, `ENCODE CLEARLY`, `INSTRUCTIONS`, etc.

**Result**: ✅ **WORKED** - Noise text was successfully filtered out before clustering

---

### 2. Simplified Question Detection
**Implementation**: Modified `detect_question_start_enhanced()` to only look for strict number pattern `^\s*(\d{1,3})\.` without bold/font checks.

**Rationale**: Trust the regex pattern, let the Assembler combine it with clustering signal.

**Result**: ✅ **WORKED** - Pattern detection was consistent

---

### 3. Hybrid Signal in Assembler
**Implementation**: Modified `StructureAssembler.assemble()` to require BOTH signals:
```python
is_valid_start = (is_new_cluster and q_start_res) or (current_mcq is None and q_start_res)
```

**Rationale**: A new question must be:
- A new cluster (spatial gap detected by HDBSCAN) AND
- Match the number pattern (1., 2., 3., etc.)

**Result**: ⚠️ **PARTIALLY WORKED** - Logic was sound, but clustering quality was poor

---

### 4. HDBSCAN Clustering Configuration
**Initial Config**:
- `MIN_CLUSTER_SIZE`: 2
- `MIN_SAMPLES`: 1

**Problem**: ValueError when single block in column

**Fix**: Added edge case handling for single-block columns

**Adjustment**: Increased `MIN_CLUSTER_SIZE` to 15 (assuming typical question has 50-100 words)

**Result**: ❌ **DID NOT WORK** - Too aggressive, missed most questions

---

### 5. Page Filtering
**Issue**: Confusion between 0-indexed and 1-indexed page numbers

**Fix**: Changed to `SKIP_PAGES: [1]` with comment clarifying it's 1-indexed

**Result**: ✅ **WORKED** - Instructions page successfully skipped

---

## What Didn't Work

### Root Cause Analysis

The clustering approach **fundamentally failed** because:

1. **Text Granularity Mismatch**
   - PDF extraction produces **word-level or line-level** text blocks
   - A single question might produce 50-100 separate text blocks
   - HDBSCAN clusters based on vertical position (Y-coordinate)
   - Result: Each question creates **multiple micro-clusters** instead of one cluster

2. **Inconsistent Spacing Patterns**
   - VisionIAS PDFs have variable spacing WITHIN questions
   - Some lines are tightly packed, others have gaps
   - Options may have similar spacing to question starts
   - HDBSCAN cannot reliably distinguish "question boundary gap" from "intra-question gap"

3. **Hybrid Signal Too Strict**
   - Requiring BOTH (cluster break AND number pattern) misses valid questions
   - Many numbered lines (1., 2., 3.) appear WITHIN question text (e.g., "1. Statement is correct")
   - These create false positives for question_start detection
   - Clustering breaks happen randomly due to spacing variations

### Evidence from Test Run

**Expected**: ~100 MCQs  
**Actual**: 23 MCQs

**Example of failure** (Q7):
```
Q7: Consider the following statements regarding the National Commission 
    of Scheduled Tribes (NCST): ...
  (a) It is the only species of wolf that is found in India.
  (b) It is naturally found in the Trans-Himalayan region only.
```

The options are from a **completely different question** about wolves, proving that question boundaries were not detected correctly.

---

## Clustering Analysis Results

From examining `01_analyzed_document.json`:

```
Block 11: "2."
  Cluster: 7 | New Cluster: True | Question Start: True

Block 12: "How many of the following protections are"
  Cluster: 7 | New Cluster: False

Block 13: "available as a fundamental right under the"
  Cluster: 12 | New Cluster: True  // ❌ Unexpected break!

Block 15: "preventive detention law?"
  Cluster: 13 | New Cluster: True  // ❌ Another unexpected break!

Block 16: "1. The grounds of detention should be"
  Cluster: 13 | New Cluster: False | Question Start: True
  // ❌ Incorrectly detected as question start (it's a numbered statement)
```

**Observations**:
- Question text spanning 5 blocks produced **4 different clusters** (7, 12, 13)
- New clusters appeared in the middle of sentences
- Numbered statement "1. The grounds..." triggered false positive question detection

---

## What We Learned

### Clustering is Not the Right Tool Here

**Why it fails**:
1. Requires **consistent spatial patterns** - VisionIAS PDFs don't have this
2. Works best with **paragraph-level** granularity - we have **word-level** granularity
3. Assumes gaps between clusters are **larger and consistent** - not true in dense MCQ layouts

### Better Approaches to Consider

1. **Pure Heuristic Approach** (Original)
   - Use vertical spacing analysis (already have `analyze_vertical_break`)
   - Combine with font styling, indentation patterns
   - More interpretable and tunable

2. **Sequence Labeling / NER Approach**
   - Treat as a sequence tagging problem
   - Train a model to label each text block: [Q_START, Q_CONT, OPT_A, OPT_B, ...]
   - Would handle variable spacing naturally

3. **Vision-Based Approach**
   - Use layout detection models (LayoutLM, YOLO, etc.)
   - Directly detect bounding boxes of questions/options from PDF images
   - More robust to formatting variations

4. **Improved Extraction**
   - Extract at **sentence-level** or **logical-block-level** instead of word-level
   - Use PyMuPDF's block structure more intelligently
   - Reduce granularity before applying clustering

---

## Recommendations

### Immediate Fix
- **Revert to spacing-based heuristics** with refined parameters
- Use vertical spacing multipliers (SMALL_BREAK, MEDIUM_BREAK, LARGE_BREAK)
- Combine with font size, boldness, and indentation signals

### Medium Term
- Investigate sentence-level extraction to reduce text block granularity
- Build a small labeled dataset of VisionIAS questions
- Fine-tune spacing thresholds empirically

### Long Term
- Consider ML-based sequence labeling approach if heuristics remain brittle
- Evaluate vision-based PDF parsing libraries (e.g., layout-parser, unstructured.io)

---

## Code Changes Made

### Files Modified:
1. ✅ `config.py` - Added NOISE_PATTERNS, refined vision_ias_questions config
2. ✅ `pymupdf_extractor.py` - Added noise filtering
3. ✅ `pdf_parser.py` - Added noise filtering, fixed config access
4. ✅ `patterns.py` - Simplified detect_question_start_enhanced
5. ✅ `orchestrator.py` - Implemented hybrid signal logic
6. ✅ `clustering.py` - Fixed single-sample edge case

### Current State:
- Code runs without errors
- Noise filtering works well
- Clustering produces results, but they are **inaccurate**
- Parser extracts 23 MCQs instead of ~100 (77% missed)
- Question-option matching is broken

---

## Diagnostic Scripts Used

### Script 1: Quick MCQ Count and Preview
```python
# Check extracted MCQs
import json
data = json.load(open('output/02_final_mcqs.json'))
print(f'Total MCQs: {len(data)}')
print('\n--- First 3 MCQs ---')
for i, mcq in enumerate(data[:3]):
    print(f'Q{mcq["question_number"]}: {mcq["question_text"]}')
    for k, v in mcq['options'].items():
        print(f'  ({k}) {v}')
    print()
```

### Script 2: Analyze Clustering Results
```python
# Examine clustering behavior on a specific page
import json
data = json.load(open('output/01_analyzed_document.json'))
pages = data['pages']

# Check page 2 (index 1) which should have actual questions
if len(pages) > 1:
    page2 = pages[1]
    all_blocks = page2['left_column_blocks'] + page2['right_column_blocks']
    print(f'Page 2 - Total blocks: {len(all_blocks)}')
    print('\n--- First 15 text blocks from Page 2 ---')
    for i, block in enumerate(all_blocks[:15]):
        print(f'{i+1}. {block["text"][:150]}')
        # Check if it has clustering info
        for result in block.get('analysis_results', []):
            if result.get('heuristic_name') == 'hdbscan_clustering':
                print(f'   Cluster: {result.get("cluster_label")} | New Cluster: {result.get("is_new_cluster")}')
            if result.get('heuristic_name') == 'question_start':
                print(f'   Question Start: {result.get("is_question_start")} | Q# {result.get("question_number")}')
        print()
```

### Script 3: Deep Dive into Question Boundary Detection
```python
# Analyze a specific question area with block IDs
import json
data = json.load(open('output/01_analyzed_document.json'))
pages = data['pages']

if len(pages) > 1:
    page2 = pages[1]
    all_blocks = page2['left_column_blocks'] + page2['right_column_blocks']
    print('--- Blocks 11-30 from Page 2 (Question 2 area) ---')
    for i in range(10, min(30, len(all_blocks))):
        block = all_blocks[i]
        print(f'{i+1}. [{block.get("id", "")}] {block["text"][:100]}')
        # Check if it has clustering info
        for result in block.get('analysis_results', []):
            if result.get('heuristic_name') == 'hdbscan_clustering':
                print(f'   Cluster: {result.get("cluster_label")} | New: {result.get("is_new_cluster")}')
            if result.get('heuristic_name') == 'question_start':
                print(f'   Question Start: {result.get("is_question_start")} | Q# {result.get("question_number")}')
        print()
```

### Script 4: Check Noise Filtering
```python
# Verify noise patterns were filtered
import json
data = json.load(open('output/01_analyzed_document.json'))
pages = data['pages']

first_page = pages[0]
all_blocks = first_page['left_column_blocks'] + first_page['right_column_blocks']
print(f'Total pages: {len(pages)}')
print('\n--- First 10 text blocks from Page 1 ---')
for i, block in enumerate(all_blocks[:10]):
    print(f'{i+1}. {block["text"][:100]}')
```

### How to Run
```bash
cd /home/abhishek/Downloads/experiments/ai-tools/reformatting

# Run the parser
python qna_orchestrator/qna_heuristics/main.py \
  /home/abhishek/Downloads/chrome/search_space/prelims/2025_vision/4701_Q_1_.pdf \
  --parser vision_ias_questions

# Then run diagnostic scripts
python -c "$(cat script1.py)"
```

---

## Conclusion

The clustering approach, while theoretically sound, **does not work for VisionIAS PDFs** due to:
- Text extraction granularity mismatch
- Inconsistent spacing patterns
- Difficulty distinguishing question boundaries from intra-question gaps

**Next steps**: Revert to refined heuristic-based approach with better spacing analysis and pattern matching.
