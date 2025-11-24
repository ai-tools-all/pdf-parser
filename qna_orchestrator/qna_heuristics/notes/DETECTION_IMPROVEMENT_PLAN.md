# MCQ Detection Improvement Plan (Updated)

## Current Issues Analysis

### Major Problems Identified
1. **Question "b"** - System is detecting an answer explanation as a question
2. **Missing Question 1** - The actual first question "Consider the following statements:" is not being detected
3. **Text Flow Problem** - System isn't properly handling left-to-right column flow
4. **Answer Detection** - "Ans: (b)" pattern is being detected but not properly handled
5. **Column Confusion** - Text from different columns getting merged incorrectly

## Implementation Plan (Revised Based on User Feedback)

### Phase 1: Layout Detection (HIGHEST PRIORITY)
**Rationale**: Layout detection must happen first to provide context for all other heuristics

**Requirements from User:**
- Two column layout (vertical/horizontal)
- Header detection
- Footer detection (colored background text)
- User-configurable layout parameters in config.py

**Solutions:**
- [ ] Enhance PDF parser to detect layout early in processing
- [ ] Add configurable layout types in config.py
- [ ] Implement header/footer detection with configurable regions
- [ ] Provide layout context to all subsequent heuristics

**Files to modify:**
- `config.py` - Add layout configuration section
- `pdf_parser.py` - Enhanced layout detection
- `data_models.py` - Add layout context to AnalysisContext

### Phase 2: Configurable Multi-Signal Question Detection
**User Requirements:**
Question detection should use multiple configurable signals:
1. **Indentation** - Questions aligned to the left
2. **Number Pattern** - Starting with number (or any user-defined regex)
3. **Bold Text** - First line of question has bold formatting
4. **Spacing** - Spacing-based heuristics for question boundaries

**Key Point**: Handle numbered sub-statements (1., 2., 3.) within questions while detecting question start/end boundaries

**Solutions:**
- [ ] Create configurable signal system in config.py
- [ ] Implement signal combination logic with user-defined weights
- [ ] Handle nested numbered statements within questions
- [ ] Focus on question boundary detection (begin/end)

**Files to modify:**
- `config.py` - Add signal configuration
- `heuristics/patterns.py` - Flexible pattern matching
- `orchestrator.py` - Signal combination logic

### Phase 3: Proper Text Flow (Reading Order)
**Issue**: Current system processes left column completely, then right column

**Solutions:**
- [ ] Implement proper reading order: top of left column → top of right column → next section
- [ ] Create block sorting by Y-coordinate across both columns
- [ ] Use layout context from Phase 1
- [ ] Ensure question parts from both columns are properly assembled

**Files to modify:**
- `orchestrator.py` - Update assembly logic in `StructureAssembler.assemble()`
- `pdf_parser.py` - Ensure proper block ordering

### Phase 4: Configurable Answer/Explanation Detection
**User Requirements:**
- Use combined approach: regex + other user-defined patterns
- Make these functions applicable to any block
- Separate answers from explanations cleanly

**Solutions:**
- [ ] Create configurable pattern system for answers
- [ ] Implement generic pattern application functions
- [ ] Proper state machine for question → options → answer → explanation flow
- [ ] User-configurable answer patterns

**Files to modify:**
- `config.py` - Add answer detection patterns
- `heuristics/patterns.py` - Generic pattern functions
- `orchestrator.py` - Enhanced state machine

## Detailed Implementation Steps

### Step 1: Enhanced Configuration System
```yaml
# config.py additions
LAYOUT:
  TYPE: "two_column_vertical"
  HEADER_PERCENT: 0.12
  FOOTER_PERCENT: 0.90
  COLUMN_GAP_THRESHOLD: 0.05
  
QUESTION_DETECTION:
  SIGNALS:
    indentation:
      enabled: true
      weight: 0.3
      threshold: 15.0
    number_pattern:
      enabled: true
      weight: 0.4
      regex: '^\s*(\d+)\.'
    bold_text:
      enabled: true
      weight: 0.2
    spacing:
      enabled: true
      weight: 0.3
      multiplier: 2.0
  CONFIDENCE_THRESHOLD: 0.6

ANSWER_DETECTION:
  PATTERNS:
    - regex: '^Ans:\s*\(?([a-d])\)?'
      type: 'answer_marker'
      weight: 1.0
    - regex: '^Answer:\s*\(?([a-d])\)?'
      type: 'answer_marker'
      weight: 0.8
```

### Step 2: Signal-Based Question Detection
```python
def detect_question_start(block, context, config):
    signals = {}
    total_weight = 0
    
    for signal_name, signal_config in config['QUESTION_DETECTION']['SIGNALS'].items():
        if signal_config['enabled']:
            signal_value = apply_signal(signal_name, block, context, signal_config)
            signals[signal_name] = signal_value * signal_config['weight']
            total_weight += signal_config['weight']
    
    confidence = sum(signals.values()) / total_weight
    return confidence > config['QUESTION_DETECTION']['CONFIDENCE_THRESHOLD']
```

### Step 3: Layout-Aware Processing
```python
def process_with_layout(document):
    for page in document.pages:
        layout_type = detect_layout_type(page)
        if layout_type == "two_column_vertical":
            blocks = get_reading_order_blocks(page.left_column_blocks, page.right_column_blocks)
        else:
            blocks = get_single_column_blocks(page)
        
        process_blocks_in_order(blocks, layout_context)
```

## Priority Order (Updated)

1. **PHASE 1 - Layout Detection** (Must be first)
   - `pdf_parser.py` - Layout detection
   - `config.py` - Layout configuration
   
2. **PHASE 2 - Signal-Based Question Detection**
   - `config.py` - Signal configuration
   - `heuristics/patterns.py` - Pattern functions
   - `orchestrator.py` - Signal combination
   
3. **PHASE 3 - Text Flow**
   - `orchestrator.py` - Reading order logic
   
4. **PHASE 4 - Answer Detection**
   - `config.py` - Answer patterns
   - `heuristics/patterns.py` - Answer functions
   - `orchestrator.py` - State machine

## Key Design Principles (Based on User Feedback)

1. **Configuration-Driven**: All detection parameters should be user-configurable
2. **Signal-Based**: Use multiple signals with configurable weights
3. **Layout-First**: Layout detection provides context for all other processing
4. **Flexible Patterns**: Generic pattern functions that work on any block
5. **Question Boundary Focus**: Emphasize detecting where questions begin and end
6. **Handle Nested Content**: Properly handle numbered sub-statements within questions

## Success Metrics
- [ ] Question 1 properly detected with "Consider the following statements:"
- [ ] All numbered sub-statements (1., 2., 3.) included in question body
- [ ] Clean separation between questions
- [ ] Proper column-aware text flow
- [ ] Configurable detection parameters working correctly