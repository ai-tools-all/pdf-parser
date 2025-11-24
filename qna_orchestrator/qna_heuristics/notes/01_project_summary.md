# Project Summary: MCQ Detection Enhancement

This document summarizes the judgement calls, decisions, and learnings from the project to enhance MCQ detection.

## 1. Judgement Calls and Decisions

*   **Adopted a Phased Approach:** The project was broken down into three distinct phases: Core Heuristics Implementation, Orchestrator and Configuration Updates, and Refinement and Verification. This allowed for a structured and manageable workflow.
*   **Prioritized Heuristics:** The new heuristics were implemented first, as they formed the foundation of the improved detection logic. This decision was based on the `updated_mcq_detection_plan.md`.
*   **Refactored Orchestrator:** Instead of patching the existing orchestrator, a significant refactoring was undertaken to fully leverage the new heuristics. This was a key decision to move away from a complex state machine to a more streamlined, classification-based approach.
*   **Deprecation of Old Heuristics:** The old, pattern-based heuristics were deprecated and removed to avoid code bloat and potential conflicts with the new, more robust system.
*   **Iterative Debugging:** The final verification phase involved a series of runs and fixes, demonstrating an iterative approach to debugging and problem-solving.

## 2. False Paths and Learnings

This section outlines the errors encountered during the implementation, the fixes, and the key learnings.

### 2.1. `AttributeError: 'AnalysisContext' object has no attribute 'page_data'`

*   **File:** `heuristics/layout.py`
*   **Code Snippet (Incorrect):**
    ```python
    left_blocks = context.page_data.get('left_column_blocks', [])
    ```
*   **Learning:** The `AnalysisContext` object did not have the `page_data` attribute. This was a missing piece of context that the new `sequence_column_content` heuristic required. The fix involved updating the `AnalysisContext` data model and the orchestrator to pass this data through. This highlighted the importance of ensuring all necessary data is available in the context object when adding new heuristics.

### 2.2. `NameError: name 'Page' is not defined`

*   **File:** `orchestrator.py`
*   **Code Snippet (Incorrect):**
    ```python
    def _analyze_scope(self, blocks: List[TextBlock], page: Page):
    ```
*   **Learning:** A simple but common error. The `Page` type hint was used without being imported. This emphasizes the need for careful dependency management and ensuring all necessary modules are imported.

### 2.3. `AttributeError: 'Page' object has no attribute 'get'`

*   **File:** `heuristics/layout.py`
*   **Code Snippet (Incorrect):**
    ```python
    left_blocks = context.page_data.get('left_column_blocks', [])
    ```
*   **Learning:** This error was a direct result of the previous fix. While `page_data` was now available, it was a dataclass object, not a dictionary. The code was incorrectly trying to use the `.get()` method. The fix was to use direct attribute access (`context.page_data.left_column_blocks`). This learning reinforces the importance of understanding the data structures being passed between different parts of the application.

### 2.4. `TypeError: 'TextBlock' object is not subscriptable`

*   **File:** `heuristics/layout.py`
*   **Code Snippet (Incorrect):**
    ```python
    left_sorted = sorted(left_blocks, key=lambda b: b['bbox'][1])
    ```
*   **Learning:** Similar to the previous error, this was caused by treating a `TextBlock` object as a dictionary. The fix was to use attribute access (`b.bbox`). This again highlights the need to be mindful of the object types being handled.

### 2.5. `AttributeError: 'AnalysisContext' object has no attribute 'previous_analysis'`

*   **File:** `heuristics/patterns.py`
*   **Code Snippet (Incorrect):**
    ```python
    if is_indented or (context.previous_analysis and context.previous_analysis.get("type") == "answer"):
    ```
*   **Learning:** The `classify_content_type` heuristic required context about the previously analyzed block. This was not available in the `AnalysisContext`. The fix involved adding `previous_analysis` to the data model and updating the orchestrator to pass this information. This was a good example of how context needs to be expanded as the system's intelligence grows.

### 2.6. `AttributeError: 'StructureAssembler' object has no attribute '_merge_mcqs'`

*   **File:** `orchestrator.py`
*   **Learning:** This was a simple mistake made during the refactoring of the `StructureAssembler`. The `_merge_mcqs` method was accidentally deleted. This serves as a reminder to be careful when performing large-scale refactoring and to ensure all necessary components are preserved.
