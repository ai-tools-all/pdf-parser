# Enhanced Question Detection Heuristics - Implementation Plan

## Executive Summary

This plan details the implementation of enhanced question detection heuristics for the QNA orchestrator system based on analysis of current output issues and user requirements.

## Current System Analysis

### Existing Architecture
- **File**: `orchestrator.py` (213 lines)
- **Current Flow**: PDF Parser → Heuristics Analysis → Structure Assembly → MCQ Output
- **Issue**: Questions are fragmented and poorly detected (see `03_final_mcqs.json`)

### Current Problems Identified
1. **Question fragmentation**: "Consider the following statements:" appears as separate MCQ entries
2. **Missing content**: Empty options/answers in many entries  
3. **Poor boundary detection**: Multiple entries for same question number
4. **Layout confusion**: Two-column content not properly handled

### Current Heuristics Structure
```python
# From orchestrator.py lines 23-33
def _load_heuristics(self):
    loaded_funcs = []
    for path in self.config["ACTIVE_HEURISTICS"]:
        module_path, func_name = path.rsplit('.', 1)
        # Load from heuristics/ directory
```

Existing heuristics modules:
- `heuristics/layout.py`
- `heuristics/patterns.py` 
- `heuristics/spacing.py`

## New Heuristics Requirements

### 1. Bold Text Detection
**Target Pattern**: First line of question is in bold formatting
**Implementation Location**: `heuristics/patterns.py`

```python
def detect_bold_formatting(context: AnalysisContext) -> Optional[Dict]:
    """Detect bold text formatting which often indicates question starts"""
    block = context.current_block
    
    # Check if bold formatting (font weight or font name indicators)
    is_bold = block.font_weight > 600 or 'bold' in block.font_name.lower()
    
    if is_bold:
        return {
            "heuristic_name": "font_style",
            "is_bold": True,
            "confidence": 0.8
        }
    return None
```

### 2. Answer Detection with "Ans:" Keyword
**Target Pattern**: "Ans: b" followed by indented explanation
**Implementation Location**: `heuristics/patterns.py`

```python
def detect_answer_with_explanation(context: AnalysisContext) -> Optional[Dict]:
    """Detect answer markers and explanations"""
    block = context.current_block
    
    # Pattern: "Ans: X" where X is answer option
    ans_pattern = r'^Ans:\s*([abcd]|[1-4])\s*'
    match = re.match(ans_pattern, block.text.strip(), re.IGNORECASE)
    
    if match:
        return {
            "heuristic_name": "answer_detection",
            "type": "answer_marker",
            "answer_value": match.group(1).lower(),
            "has_explanation": len(block.text.strip()) > len(match.group(0)),
            "confidence": 0.95
        }
    
    # Check for indented explanation text
    is_indented = context.current_block.bbox[0] > context.scope_min_x + 20
    if is_indented and context.previous_block:
        prev_analysis = get_block_analysis(context.previous_block, "answer_detection")
        if prev_analysis and prev_analysis.get("type") == "answer_marker":
            return {
                "heuristic_name": "answer_detection", 
                "type": "explanation_text",
                "is_indented": True,
                "confidence": 0.8
            }
    
    return None
```

### 3. Two-Column Layout Detection
**Implementation Location**: `heuristics/layout.py`
**Logic Reference**: From `A004_line_spacing_wihtA003.py:85-120`

```python
def detect_column_boundaries(context: AnalysisContext) -> Optional[Dict]:
    """Detect column transitions and boundaries"""
    blocks = context.all_blocks_in_scope
    
    # Calculate column separator position
    x_positions = [b.bbox[0] for b in blocks]
    page_width = max(b.bbox[2] for b in blocks)
    
    # Find natural break around middle
    middle_x = page_width / 2
    left_blocks = [b for b in blocks if b.bbox[0] < middle_x]
    right_blocks = [b for b in blocks if b.bbox[0] >= middle_x]
    
    if len(left_blocks) > 0 and len(right_blocks) > 0:
        separator_x = (max(b.bbox[2] for b in left_blocks) + 
                      min(b.bbox[0] for b in right_blocks)) / 2
        
        current_block = context.current_block
        column = "left" if current_block.bbox[0] < separator_x else "right"
        
        return {
            "heuristic_name": "column_layout",
            "column": column,
            "separator_position": separator_x,
            "confidence": 0.9
        }
    
    return None
```

### 4. Line Spacing Analysis  
**Implementation Location**: `heuristics/spacing.py`
**Logic Reference**: From `A004_line_spacing_wihtA003.py:140-180`

```python
def analyze_vertical_spacing_patterns(context: AnalysisContext) -> Optional[Dict]:
    """Enhanced spacing analysis for question boundaries"""
    
    if not context.previous_block:
        return None
        
    current = context.current_block
    previous = context.previous_block
    
    # Calculate gap between blocks
    gap = current.bbox[1] - previous.bbox[3]
    median_spacing = context.scope_median_spacing
    
    # Define spacing thresholds
    large_gap_threshold = median_spacing * 2.0
    question_break_threshold = median_spacing * 1.5
    
    spacing_type = "normal"
    is_question_boundary = False
    
    if gap > large_gap_threshold:
        spacing_type = "large_break"
        is_question_boundary = True
    elif gap > question_break_threshold:
        spacing_type = "medium_break" 
        # Check if this could be question boundary based on content
        has_question_markers = any(pattern in current.text.lower() 
                                 for pattern in ["consider", "which", "with reference"])
        is_question_boundary = has_question_markers
    
    return {
        "heuristic_name": "enhanced_spacing",
        "spacing_type": spacing_type,
        "gap_size": gap,
        "is_question_boundary": is_question_boundary,
        "relative_gap": gap / median_spacing,
        "confidence": 0.8 if is_question_boundary else 0.6
    }
```

## Integration Plan

### Phase 1: Heuristic Implementation
1. **Add new functions** to existing heuristic modules
2. **Update config.py** to include new heuristics in `ACTIVE_HEURISTICS`
3. **Test individual heuristics** with sample data

### Phase 2: Orchestrator Enhancement
1. **Modify `_is_question_start()`** in `orchestrator.py:117-127`
```python
def _is_question_start(self, block: TextBlock, current_mcq: Optional[MCQ]) -> bool:
    # Original logic
    is_break = self._get_analysis(block, "vertical_break", "is_break", False)
    pattern_type = self._get_analysis(block, "pattern_match", "type")
    
    # NEW: Enhanced spacing logic
    enhanced_spacing = self._get_analysis(block, "enhanced_spacing", "is_question_boundary", False)
    
    # NEW: Bold text detection
    is_bold = self._get_analysis(block, "font_style", "is_bold", False)
    
    # Enhanced detection logic
    is_potential_start = (
        (is_break and pattern_type == "question_start") or
        (enhanced_spacing and is_bold)
    )
    
    if not is_potential_start:
        return False
        
    # Rest of existing logic...
```

2. **Enhance content assembly** in `orchestrator.py:188-196`
```python
# Already partially implemented - need to expand
if current_part == "question":
    is_bold = self._get_analysis(block, "font_style", "is_bold", False)
    
    # NEW: Better content filtering
    answer_detection = self._get_analysis(block, "answer_detection", "type")
    if answer_detection == "answer_marker":
        current_part = "explanation"  # Transition to explanation
    elif not pattern_type:
        current_mcq.question_text += f" {block.text.strip()}"
```

### Phase 3: Configuration Updates

**File**: `config.py`
```python
DEFAULT_CONFIG = {
    "ACTIVE_HEURISTICS": [
        "heuristics.spacing.detect_vertical_breaks",
        "heuristics.spacing.analyze_vertical_spacing_patterns",  # NEW
        "heuristics.patterns.detect_question_patterns", 
        "heuristics.patterns.detect_bold_formatting",            # NEW
        "heuristics.patterns.detect_answer_with_explanation",    # NEW
        "heuristics.layout.detect_indentation",
        "heuristics.layout.detect_column_boundaries"             # NEW
    ],
    "HEURISTICS": {
        "PATTERNS": {
            # Existing patterns...
        },
        "SPACING": {
            # Enhanced thresholds                                 # NEW
            "QUESTION_BOUNDARY_MULTIPLIER": 1.5,
            "LARGE_BREAK_MULTIPLIER": 2.0
        }
    }
}
```

## Testing Strategy

### Test Cases
1. **Bold intro detection**: "Consider the following statements:" should be detected as question start
2. **Answer parsing**: "Ans: b The explanation..." should separate answer from explanation  
3. **Column handling**: Content from both columns should be properly sequenced
4. **Spacing boundaries**: Large gaps should indicate question boundaries

### Expected Improvements
- Reduce question fragmentation from current ~10 fragments per question to 1
- Properly populate options and answers (currently many are empty)
- Maintain question numbering consistency
- Improve content coherence

## Implementation Order

1. ✅ **Analysis Phase** - Understand current system and issues
2. **Heuristic Development** - Implement 4 new heuristic functions
3. **Integration** - Modify orchestrator logic 
4. **Configuration** - Update config with new heuristics
5. **Testing** - Validate against existing JSON output
6. **Refinement** - Adjust thresholds and logic based on results

## Success Metrics

- **Fragmentation Reduction**: < 2 MCQ entries per actual question
- **Content Completeness**: > 90% of questions have populated options and answers
- **Boundary Accuracy**: Question boundaries detected with > 85% accuracy
- **Column Handling**: Proper sequencing of two-column content

## Risk Mitigation

- **Gradual Integration**: Test each heuristic individually before full integration
- **Fallback Logic**: Maintain existing logic as fallback if new heuristics fail
- **Configuration Flexibility**: Make thresholds configurable for easy tuning
- **Debug Output**: Enhanced logging to trace heuristic decisions

## Files to Modify

1. `heuristics/patterns.py` - Add 2 new functions
2. `heuristics/spacing.py` - Add 1 enhanced function  
3. `heuristics/layout.py` - Add 1 column detection function
4. `orchestrator.py` - Modify question detection and assembly logic
5. `config.py` - Add new heuristics and configuration options

## Estimated Timeline

- **Phase 1**: 2-3 hours (heuristic implementation)
- **Phase 2**: 2-3 hours (orchestrator integration)  
- **Phase 3**: 1 hour (configuration and testing)
- **Total**: 5-7 hours of development time

---

*Plan created: 2025-06-26*
*Status: Ready for approval and implementation*