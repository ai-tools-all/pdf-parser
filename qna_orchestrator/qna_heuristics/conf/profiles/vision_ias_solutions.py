# Specific settings for VisionIAS Solutions PDF

PROFILE = {
    "DEFAULT_PARSER": "vision_ias_solutions",
    
    # Use Vision Solutions assembly strategy (header-based extraction)
    "ASSEMBLY_STRATEGY": "vision_solutions",
    
    "PARSERS": {
        "vision_ias_solutions": {
            "type": "heuristic_based",
            # New Feature: precise page control
            "PAGE_RANGE": None,  # None = All, or tuple (start_page, end_page) e.g. (1, 38)
            "SKIP_PAGES": [],
        }
    },

    "NOISE_PATTERNS": [
        "www.visionias.in",
        "©Vision IAS",
        "https://upscpdf.com/",
        "ANSWERS & EXPLANATIONS",
        "GENERAL STUDIES (P) TEST"
    ],

    # Sequential parser uses basic signals for solutions
    "ACTIVE_HEURISTICS": [
        "qna_orchestrator.qna_heuristics.heuristics.patterns.detect_question_start_enhanced",
        "qna_orchestrator.qna_heuristics.heuristics.patterns.classify_content_type",
    ],

    "HEURISTICS": {
        "PATTERNS": {
            # Captures "Q 1.C", "Q 100.A"
            # Group 1: Question Number, Group 2: Correct Option
            "REGEX_SOLUTION_HEADER": r'^\s*Q\s*(\d{1,3})\s*\.\s*([A-D])',
        }
    }
}
