# Updated MCQ Detection Plan - Based on Input/Output Analysis

## Executive Summary

After analyzing the actual input (`01_raw_document.json`) and output (`03_final_mcqs.json`), this updated plan addresses the specific issues observed in the current MCQ detection system.

## Critical Issues Identified from Data Analysis

### Input Structure Analysis (`01_raw_document.json`)
- **Font Detection Available**: Raw data contains `font_name` (e.g., "Calibri-Bold") and `font_size`
- **Two-Column Layout**: Clear separation with `left_column_blocks` and `right_column_blocks`
- **Precise Positioning**: Exact `bbox` coordinates available for spatial analysis
- **Question Numbering**: Questions start with "1.\t Consider the following statements:"

### Output Problems (`03_final_mcqs.json`)
1. **Severe Fragmentation**: 
   - Question fragments like `"question_number": "b"` with answer text as question
   - Question fragments like `"question_number": "a"` containing "Ans: (a)" explanations
   - Incomplete questions with missing options/answers

2. **Content Misclassification**:
   - Answer explanations appearing as question text
   - Question numbers extracted incorrectly (letters instead of numbers)
   - Options completely missing in many entries

3. **Assembly Logic Failures**:
   - "Consider the following statements:" appearing as separate incomplete questions
   - Multi-part questions split across multiple MCQ entries
   - Answer explanations not properly separated from question content

## Root Cause Analysis

### Current System Weaknesses
1. **Poor Question Boundary Detection**: Cannot distinguish between question starts and continuation text
2. **Answer Pattern Confusion**: "Ans: (a)" patterns treated as question starts instead of answer markers
3. **Column Sequencing Issues**: Two-column content not properly ordered
4. **Font Style Ignored**: Bold formatting not used for question detection despite being available

## Enhanced Detection Strategy

### 1. Question Start Detection (Priority: Critical)
**Target Pattern**: Bold text + Question number + Question keywords
```python
def detect_question_start_enhanced(context: AnalysisContext) -> Optional[Dict]:
    """Enhanced question start detection using multiple signals"""
    block = context.current_block
    
    # Signal 1: Bold formatting
    is_bold = 'bold' in block.font_name.lower() or block.font_weight > 600
    
    # Signal 2: Question number pattern
    question_num_pattern = r'^\d+\.\s*'
    has_question_number = re.match(question_num_pattern, block.text.strip())
    
    # Signal 3: Question keywords
    question_keywords = ['consider the following', 'which of the following', 'with reference to']
    has_question_keyword = any(keyword in block.text.lower() for keyword in question_keywords)
    
    # Combined detection
    if is_bold and has_question_number and has_question_keyword:
        return {
            "heuristic_name": "enhanced_question_start",
            "confidence": 0.95,
            "question_number": has_question_number.group().strip('.\t '),
            "is_question_start": True
        }
    
    return None
```

### 2. Answer Boundary Detection (Priority: Critical)
**Target Pattern**: "Ans: (option)" followed by explanation
```python
def detect_answer_boundaries(context: AnalysisContext) -> Optional[Dict]:
    """Detect answer markers and separate from explanations"""
    block = context.current_block
    
    # Pattern: "Ans: (a)" or "Ans: a"
    ans_pattern = r'^Ans:\s*\(?([abcd]|[1-4])\)?'
    match = re.match(ans_pattern, block.text.strip(), re.IGNORECASE)
    
    if match:
        answer_value = match.group(1).lower()
        explanation_start = match.end()
        explanation_text = block.text[explanation_start:].strip()
        
        return {
            "heuristic_name": "answer_boundary",
            "type": "answer_marker",
            "answer": answer_value,
            "has_explanation": len(explanation_text) > 0,
            "explanation_text": explanation_text,
            "confidence": 0.98
        }
    
    return None
```

### 3. Column Sequencing (Priority: High)
**Issue**: Two-column content needs proper ordering
```python
def sequence_column_content(context: AnalysisContext) -> Optional[Dict]:
    """Ensure proper sequencing of two-column content"""
    
    # Get all blocks in current scope
    left_blocks = context.page_data.get('left_column_blocks', [])
    right_blocks = context.page_data.get('right_column_blocks', [])
    
    # Sort by vertical position within each column
    left_sorted = sorted(left_blocks, key=lambda b: b['bbox'][1])
    right_sorted = sorted(right_blocks, key=lambda b: b['bbox'][1])
    
    # Determine reading order based on vertical alignment
    current_block = context.current_block
    
    return {
        "heuristic_name": "column_sequencing",
        "column": "left" if current_block in left_blocks else "right",
        "reading_order": determine_reading_order(left_sorted, right_sorted, current_block),
        "confidence": 0.9
    }
```

### 4. Content Classification (Priority: High)
**Issue**: Need to classify text blocks as question/option/answer/explanation
```python
def classify_content_type(context: AnalysisContext) -> Optional[Dict]:
    """Classify text blocks into content types"""
    block = context.current_block
    text = block.text.strip()
    
    # Question content (bold + question patterns)
    if 'bold' in block.font_name.lower() and any(pattern in text.lower() 
                                                for pattern in ['consider', 'which', 'with reference']):
        return {"heuristic_name": "content_classification", "type": "question", "confidence": 0.9}
    
    # Option content (a), b), c), d) patterns)
    option_pattern = r'^\(?([abcd])\)?\s+'
    if re.match(option_pattern, text, re.IGNORECASE):
        return {"heuristic_name": "content_classification", "type": "option", "confidence": 0.85}
    
    # Answer marker
    if re.match(r'^Ans:\s*', text, re.IGNORECASE):
        return {"heuristic_name": "content_classification", "type": "answer", "confidence": 0.95}
    
    # Explanation (indented or following answer)
    is_indented = block.bbox[0] > context.scope_min_x + 20
    if is_indented or context.previous_analysis.get("type") == "answer":
        return {"heuristic_name": "content_classification", "type": "explanation", "confidence": 0.7}
    
    return {"heuristic_name": "content_classification", "type": "continuation", "confidence": 0.5}
```

## Implementation Plan

### Phase 1: Core Heuristics (Week 1)
1. **Enhanced Question Start Detection** - `heuristics/patterns.py`
2. **Answer Boundary Detection** - `heuristics/patterns.py`
3. **Content Classification** - `heuristics/patterns.py`
4. **Column Sequencing** - `heuristics/layout.py`

### Phase 2: Orchestrator Updates (Week 1)
1. **Question Assembly Logic** - Modify `orchestrator.py:_assemble_question()`
2. **Content Filtering** - Prevent answer text from becoming question text
3. **Boundary Detection** - Use enhanced heuristics for question boundaries
4. **Option Extraction** - Properly extract and format options

### Phase 3: Configuration & Testing (Week 1)
1. **Config Updates** - Add new heuristics to `ACTIVE_HEURISTICS`
2. **Threshold Tuning** - Adjust confidence thresholds based on testing
3. **Validation** - Test against current output to measure improvements

## Expected Improvements

### Quantitative Targets
- **Fragmentation Reduction**: From 20+ fragments per question to 1 complete question
- **Content Accuracy**: >95% correct classification of question/option/answer/explanation
- **Question Completeness**: >90% of questions have all required fields populated
- **Answer Extraction**: >95% accuracy in answer detection and separation

### Qualitative Improvements
- Questions properly assembled from multiple text blocks
- Options correctly extracted and formatted
- Answers separated from explanations
- Two-column content properly sequenced
- No more answer text appearing as question content

## Critical Implementation Notes

### Data Structure Utilization
- **Font Information**: Use `font_name` containing "Bold" for question detection
- **Column Structure**: Leverage existing `left_column_blocks`/`right_column_blocks`
- **Positioning**: Use `bbox` coordinates for spatial analysis
- **Text Patterns**: Exploit consistent formatting patterns in the source

### Risk Mitigation
- **Gradual Rollout**: Test each heuristic individually before integration
- **Fallback Logic**: Maintain existing logic as backup
- **Debug Logging**: Add comprehensive logging for troubleshooting
- **Validation Metrics**: Implement automated quality checks

## Files to Modify

1. **`heuristics/patterns.py`** - Add 3 new detection functions
2. **`heuristics/layout.py`** - Add column sequencing function
3. **`orchestrator.py`** - Major updates to assembly logic
4. **`config.py`** - Add new heuristics and parameters
5. **`data_models.py`** - Potentially add new analysis result types

## Success Criteria

### Before Implementation (Current State)
- Questions fragmented into 5-10 pieces
- Many empty options/answers
- Answer text appearing as questions
- Poor content organization

### After Implementation (Target State)
- Complete, well-formed MCQ entries
- All questions have proper options and answers
- Clear separation of content types
- Logical content flow and organization

## Timeline

- **Analysis & Planning**: ✅ Complete
- **Phase 1 Implementation**: 2-3 days
- **Phase 2 Integration**: 2-3 days  
- **Phase 3 Testing**: 1-2 days
- **Total Estimated Time**: 5-8 days

---

*Updated Plan Created: 2025-06-26*  
*Based on: Actual input/output data analysis*  
*Status: Ready for implementation*