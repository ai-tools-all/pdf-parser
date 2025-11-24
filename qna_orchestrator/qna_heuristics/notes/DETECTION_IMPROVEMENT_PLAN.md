# MCQ Detection Improvement Plan

## Current Issues Analysis

### Major Problems Identified
1. **Question "b"** - System is detecting an answer explanation as a question
2. **Missing Question 1** - The actual first question "Consider the following statements:" is not being detected
3. **Text Flow Problem** - System isn't properly handling left-to-right column flow
4. **Answer Detection** - "Ans: (b)" pattern is being detected but not properly handled
5. **Column Confusion** - Text from different columns getting merged incorrectly

### Example of Current vs Expected Output

**Current Detection (WRONG):**
```
Question b: "Ans: (b) Constitutional importance as it was the first step taken..."
```

**Expected Detection (CORRECT):**
```
Question 1: "Consider the following statements:
1. It acknowledged the Company's Political and Administrative roles for the first time.
2. Governor General of Bengal was designated as Governor General of India.
3. Lord Warren Hastings was the first Governor General of Bengal.
4. The Supreme Court at Bombay was established.
5. It prohibited the servants of the Company from engaging in any private trade.
How many of the above statements are the principal features of the Regulating Act, 1773?
(a) Only two
(b) Only three  
(c) Only four
(d) All five
Ans: (b)"
```

## Implementation Plan

### Phase 1: Fix Question Number Detection
**Issue**: Current regex `^\s*(\d+)\.` only catches digits, but we need to detect "1. Consider the following..."

##>> the question detection has multiple signals. user can specify those signasls in config.py 

possible ones are 
1. indented to the left 
2. starting with number (or any given regex by user)
3. first line of the question has bold text (helpful to detect questions starting point ) 
4. spacing based hueristics  -- to understand where one question ends and another begins


it is  possibnle that the question might have multiple statements starting from numebrs, like 1. 2. 3. etc.  -- we have to handle that as well. so , the focus on is on question detection begin and end 


##>> for layout detection, user can clearly specify that in config.py 

for current needs, we need 
- two column layout -- vetical horizontal 
- header detection 
- footer detectoin -- for this case, it is the colored background text 


**Solutions:**
- [ ] Update pattern matching to handle numbered statements with bold formatting
- [ ] Add detection for "Consider the following statements:" patterns
- [ ] Implement multi-line question text assembly
- [ ] Handle sub-numbered statements (1., 2., 3., etc. within questions)

**Files to modify:**
- `heuristics/patterns.py` - Update regex patterns
- `config.py` - Add new pattern configurations

### Phase 2: Implement Proper Text Flow (Reading Order)
**Issue**: Current system processes left column completely, then right column

**Solutions:**
- [ ] Implement proper reading order: top of left column → top of right column → next section
- [ ] Create block sorting by Y-coordinate across both columns
- [ ] Ensure question parts from both columns are properly assembled
- [ ] Handle cases where questions span multiple sections

**Files to modify:**
- `orchestrator.py` - Update assembly logic in `StructureAssembler.assemble()`
- `pdf_parser.py` - Ensure proper block ordering

### Phase 3: Enhanced Question Boundary Detection 
##>> this is NOT need to be covered separately

**Issue**: Missing "Consider the following statements:" type questions

**Solutions:**
- [ ] Multi-signal detection combining:
  - Bold text detection (already implemented)
  - Numbered list pattern (1., 2., etc.)
  - Vertical spacing breaks (enhanced)
  - Descriptive question starters (already added)
- [ ] Implement confidence scoring for boundary detection
- [ ] Add fallback detection for edge cases

**Files to modify:**
- `orchestrator.py` - Update `_is_question_start()` method
- `heuristics/layout.py` - Enhance bold detection
- `heuristics/spacing.py` - Fine-tune spacing thresholds

### Phase 4: Better Answer/Explanation Separation
**Issue**: "Ans: (b)" text is being mixed with question content
 
##>>  you can use a combined appracoh for this one too. 
##>> regex given by the user + any other pattern that user decides. make these functions so that they can be applied to any block

**Solutions:**
- [ ] Proper state machine for question → options → answer → explanation flow
- [ ] Detect "Ans:" pattern and transition to answer state
- [ ] Handle explanation text that follows answers
- [ ] Separate answer choice from explanation content

**Files to modify:**
- `orchestrator.py` - Update state machine logic
- `heuristics/patterns.py` - Enhance answer detection

### Phase 5: Column-Aware Processing

##>> this must be the first part. we want to decide the layout early on which will help us understand the blocks better and apply all the heurisitcs in context of columns awware processing 


**Issue**: Text from different columns getting merged incorrectly

**Solutions:**
- [ ] Process blocks in proper reading order across both columns
- [ ] Maintain column context during assembly
- [ ] Handle questions that span both columns
- [ ] Prevent text bleeding between unrelated content

**Files to modify:**
- `orchestrator.py` - Major refactor of assembly logic
- `pdf_parser.py` - Improve column separation (already enhanced)

## Detailed Implementation Steps

### Step 1: Reading Order Fix
```python
# New algorithm for proper text flow
def get_reading_order_blocks(left_blocks, right_blocks):
    # Sort both columns by Y-coordinate
    # Interleave based on Y-position to maintain reading flow
    # Return single ordered list
```

### Step 2: Enhanced Question Detection
```python
def _is_question_start_enhanced(self, block, context):
    signals = {
        'numbered_pattern': detect_number_pattern(block.text),
        'bold_formatting': detect_bold(block.font),
        'descriptive_start': detect_descriptive_patterns(block.text),
        'vertical_spacing': analyze_spacing(context),
        'column_position': analyze_position(block.bbox)
    }
    return calculate_confidence(signals) > threshold
```

### Step 3: State Machine Enhancement
```python
states = ['question_start', 'question_body', 'sub_statements', 'options', 'answer', 'explanation']
transitions = {
    'question_start': ['question_body'],
    'question_body': ['sub_statements', 'options'],
    'sub_statements': ['options', 'question_body'],
    'options': ['answer', 'options'],
    'answer': ['explanation', 'question_start'],
    'explanation': ['question_start']
}
```

## Configuration Updates Needed

### New Regex Patterns
```yaml
PATTERNS:
  REGEX_QUESTION_NUMBERED: '^\s*(\d+)\.\s*(.+)'
  REGEX_SUB_STATEMENT: '^\s*(\d+)\.\s*(.+)'
  REGEX_DESCRIPTIVE_QUESTION: '^(Consider\s+the\s+following|Which\s+of\s+the\s+following|How\s+many)'
  REGEX_ANSWER_WITH_EXPLANATION: '^Ans:\s*\(?([a-d])\)?\s*(.*)'
```

### Enhanced Thresholds
```yaml
SPACING:
  QUESTION_BREAK_MULTIPLIER: 2.0
  SUB_STATEMENT_MULTIPLIER: 1.3
  OPTION_BREAK_MULTIPLIER: 1.5
```

## Testing Strategy

### Test Cases to Validate
1. **Question 1 Detection**: "Consider the following statements:" should be detected as question start
2. **Sub-statements**: Numbered statements within questions should be included in question text
3. **Answer Separation**: "Ans: (b)" should be separated from explanation
4. **Column Flow**: Text should flow properly across columns
5. **Multiple Questions**: Each question should be cleanly separated

### Success Metrics
- [ ] Question 1 properly detected with full text
- [ ] All numbered sub-statements included in question body
- [ ] Options properly extracted
- [ ] Answers cleanly separated from explanations
- [ ] No text bleeding between questions

## Files to Modify (Priority Order)

1. **HIGH PRIORITY**
   - `orchestrator.py` - Core assembly logic
   - `heuristics/patterns.py` - Pattern detection
   - `config.py` - Pattern configurations

2. **MEDIUM PRIORITY**
   - `heuristics/spacing.py` - Spacing thresholds
   - `heuristics/layout.py` - Bold detection refinement

3. **LOW PRIORITY**
   - `pdf_parser.py` - Column detection (already improved)
   - `data_models.py` - Structure enhancements if needed

## Rollback Plan
- Keep backup of current working files
- Implement changes incrementally with testing at each step
- Have rollback points after each phase

## Notes
- Focus on proper text flow first as it affects all other detection
- Bold detection and spacing are already enhanced from previous work
- Need to balance precision vs recall in question detection
- Test with multiple PDF layouts to ensure robustness