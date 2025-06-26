# in config.py

DEFAULT_CONFIG = {
    "DEBUG_SAVE_INTERMEDIATE": True,
    "OUTPUT_DIR": "./output",
    "PDF_PATH": "./data_dir/document.pdf", # Default path, can be overridden

    # List of heuristic functions to apply during the analysis phase
    # The orchestrator will dynamically import these.
    "ACTIVE_HEURISTICS": [
        "heuristics.spacing.analyze_vertical_break",
        "heuristics.patterns.analyze_question_number",
        "heuristics.patterns.analyze_option_letter",
        "heuristics.patterns.analyze_answer_marker",
        "heuristics.layout.analyze_indentation",
    ],

    # Parameters for the PDF Parser
    "PARSER": {
        "HEADER_REGION_PERCENT": 0.12,
        "FOOTER_REGION_PERCENT": 0.90,
    },

    # Parameters for Heuristics, organized by module
    "HEURISTICS": {
        "SPACING": {
            # A gap is a "break" if it's > N times the normal line spacing
            "BREAK_THRESHOLD_MULTIPLIER": 1.7,
            # Ignore tiny gaps when calculating normal spacing
            "MIN_GAP_FOR_NORMAL_SPACING": 0.5,
            # Ignore huge gaps (likely section breaks) for normal spacing
            "MAX_GAP_FOR_NORMAL_SPACING": 20.0,
        },
        "LAYOUT": {
            # How much horizontal space defines an indentation (in points)
            "INDENTATION_THRESHOLD": 15.0,
        },
        "PATTERNS": {
            "REGEX_QUESTION": r'^\s*(\d+)\.',
            "REGEX_OPTION": r'^\s*\(([a-zA-Z])\)',
            "REGEX_ANSWER": r'^\s*Ans:\s*\(?([a-zA-Z])\)?',
        }
    }
}