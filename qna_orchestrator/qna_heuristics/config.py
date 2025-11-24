# in config.py
import copy
import yaml
import os


DEFAULT_CONFIG = {
    "DEBUG_SAVE_INTERMEDIATE": True,
    "OUTPUT_DIR": "./output",
    "PDF_PATH": "./data_dir/document.pdf", # Default path, can be overridden

    # Default parser to use (can be overridden per run)
    "DEFAULT_PARSER": "vision_ias_questions",

    # Noise patterns to filter out during extraction
    "NOISE_PATTERNS": [
        "www.visionias.in",
        "©Vision IAS",
        "@iasvault",
        "Dark horse",
        "Test Booklet Series",
        "TEST BOOKLET",
        "GENERAL STUDIES",
        "DO NOT OPEN THIS BOOKLET",
        "INSTRUCTIONS",
        "IMMEDIATELY AFTER THE COMMENCEMENT",
        "ENCODE CLEARLY THE TEST BOOKLET SERIES",
        "You have to enter your Roll Number",
        "Time Allowed:",
        "Maximum Marks:",
        "DOES NOT HAVE ANY UNPRINTED",
        "GET IT REPLACED"
    ],

    # Parser configurations - each defines a different parser with different heuristics
    "PARSERS": {
        "default": {
            "type": "composable",
            "extraction": "pymupdf",
            "layout": "two_column",
            "analysis": "default"
        },

        "clustering_enhanced": {
            "type": "composable",
            "extraction": "pymupdf",
            "layout": "two_column",
            "analysis": "clustering_focused"
        },

        "minimal": {
            "type": "composable",
            "extraction": "pymupdf",
            "layout": "two_column",
            "analysis": "minimal_heuristics"
        },

        "vision_ias_questions": {
            "type": "heuristic_based",
            "SKIP_PAGES": [1],  # Skip page 1 (instructions page, 1-indexed)
            "ACTIVE_HEURISTICS": [
                # Run Clustering FIRST to establish boundaries
                "qna_orchestrator.qna_heuristics.heuristics.clustering.detect_cluster_break",
                "qna_orchestrator.qna_heuristics.heuristics.patterns.detect_question_start_enhanced",
                "qna_orchestrator.qna_heuristics.heuristics.patterns.classify_content_type",
                "qna_orchestrator.qna_heuristics.heuristics.layout.sequence_column_content",
            ]
        }
    },

    # Analysis strategies with different heuristic combinations
    "ANALYSIS_STRATEGIES": {
        "default": {
            "ACTIVE_HEURISTICS": [
                "qna_orchestrator.qna_heuristics.heuristics.patterns.detect_question_start_enhanced",
                "qna_orchestrator.qna_heuristics.heuristics.patterns.detect_answer_boundaries",
                "qna_orchestrator.qna_heuristics.heuristics.patterns.classify_content_type",
                "qna_orchestrator.qna_heuristics.heuristics.layout.sequence_column_content",
                "qna_orchestrator.qna_heuristics.heuristics.spacing.analyze_vertical_break",
                "qna_orchestrator.qna_heuristics.heuristics.layout.analyze_indentation",
                "qna_orchestrator.qna_heuristics.heuristics.layout.analyze_font_style",
            ]
        },

        "clustering_focused": {
            "ACTIVE_HEURISTICS": [
                "qna_orchestrator.qna_heuristics.heuristics.patterns.detect_question_start_enhanced",
                "qna_orchestrator.qna_heuristics.heuristics.patterns.detect_answer_boundaries",
                "qna_orchestrator.qna_heuristics.heuristics.patterns.classify_content_type",
                # ADD THE NEW HDBSCAN CLUSTERING HEURISTIC HERE:
                "qna_orchestrator.qna_heuristics.heuristics.clustering.detect_cluster_break",
                "qna_orchestrator.qna_heuristics.heuristics.layout.sequence_column_content",
                "qna_orchestrator.qna_heuristics.heuristics.spacing.analyze_vertical_break",
                "qna_orchestrator.qna_heuristics.heuristics.layout.analyze_indentation",
                "qna_orchestrator.qna_heuristics.heuristics.layout.analyze_font_style",
            ]
        },

        "minimal_heuristics": {
            "ACTIVE_HEURISTICS": [
                "qna_orchestrator.qna_heuristics.heuristics.patterns.detect_question_start_enhanced",
                "qna_orchestrator.qna_heuristics.heuristics.patterns.detect_answer_boundaries",
                "qna_orchestrator.qna_heuristics.heuristics.patterns.classify_content_type",
            ]
        }
    },

    # Parameters for the PDF Parser
    "PARSER": {
        "HEADER_REGION_PERCENT": 0.12,
        "FOOTER_REGION_PERCENT": 0.90,
    },

    # Parameters for Heuristics, organized by module
    "HEURISTICS": {
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
        },
        "PATTERNS": {
            # Strict number pattern for VisionIAS
            "REGEX_QUESTION": r'^\s*(\d{1,3})\.',
            "REGEX_OPTION": r'^\s*\(([a-d])\)',
            "REGEX_ANSWER": r'^\s*Ans:\s*\(?([a-d])\)?',
        },

        # NEW SECTION FOR HDBSCAN CLUSTERING
        "CLUSTERING": {
            # Minimum number of samples in a neighbourhood for a point to be a core point
            "MIN_SAMPLES": 1,
            # VisionIAS questions are dense (Question + 4 options)
            # Text blocks can be at word-level, so we need a higher threshold
            # A typical question has 50-100 words, so min cluster size of 15-20 is reasonable
            "MIN_CLUSTER_SIZE": 15
        }
    }
}

def get_config(config_path=None):
    """ 
    Loads the configuration.

    Starts with the `DEFAULT_CONFIG` and merges settings from an optional YAML file.

    Args:
        config_path (str, optional): Path to a YAML configuration file. 
                                     If provided, it will override the defaults.

    Returns:
        dict: The final configuration dictionary.
    """
    # Start with a deep copy of the default configuration
    config = copy.deepcopy(DEFAULT_CONFIG)

    # If a path is provided, load the YAML file and merge it
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            user_config = yaml.safe_load(f)
        if user_config:
            _merge_configs(config, user_config)

    return config

def _merge_configs(default, user):
    """Recursively merges the user config into the default config."""
    for key, value in user.items():
        if key in default and isinstance(default[key], dict) and isinstance(value, dict):
            _merge_configs(default[key], value)
        else:
            default[key] = value