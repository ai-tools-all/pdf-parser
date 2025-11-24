# qna_orchestrator/qna_heuristics/conf/base.py

BASE_CONFIG = {
    "DEBUG_SAVE_INTERMEDIATE": True,
    "OUTPUT_DIR": "./output",
    
    # Default parser to use
    "DEFAULT_PARSER": "default",
    
    # Parser configurations
    "PARSERS": {
        "default": {
            "type": "heuristic_based",
            "SKIP_PAGES": [],
        }
    },

    # Common/Default Heuristics used by most PDFs
    "ACTIVE_HEURISTICS": [
        "qna_orchestrator.qna_heuristics.heuristics.patterns.classify_content_type",
        "qna_orchestrator.qna_heuristics.heuristics.layout.sequence_column_content",
        "qna_orchestrator.qna_heuristics.heuristics.spacing.analyze_vertical_break",
    ],

    "PARSER": {
        "HEADER_REGION_PERCENT": 0.12,
        "FOOTER_REGION_PERCENT": 0.90,
    },

    "HEURISTICS": {
        "CLUSTERING": {
            "MIN_SAMPLES": 1,
            "MIN_CLUSTER_SIZE": 15
        },
        "PATTERNS": {
            # Standard "1." regex
            "REGEX_QUESTION": r'^\s*(\d+)\.',
            "REGEX_OPTION": r'^\s*\(([a-zA-Z])\)',
        },
        "SPACING": {
            # Enhanced multi-level break detection thresholds
            "SMALL_BREAK_MULTIPLIER": 1.2,
            "MEDIUM_BREAK_MULTIPLIER": 1.7,  # Original threshold
            "LARGE_BREAK_MULTIPLIER": 2.5,
            # Ignore tiny gaps when calculating normal spacing
            "MIN_GAP_FOR_NORMAL_SPACING": 0.5,
            # Ignore huge gaps (likely section breaks) for normal spacing
            "MAX_GAP_FOR_NORMAL_SPACING": 20.0,
        },
        "LAYOUT": {
            # How much horizontal space defines an indentation (in points)
            "INDENTATION_THRESHOLD": 15.0,
        }
    },

    # Default is empty, profiles will override this
    "NOISE_PATTERNS": []
}