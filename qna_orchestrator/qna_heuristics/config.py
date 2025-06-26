# in config.py
import copy
import yaml
import os


DEFAULT_CONFIG = {
    "DEBUG_SAVE_INTERMEDIATE": True,
    "OUTPUT_DIR": "./output",
    "PDF_PATH": "./data_dir/document.pdf", # Default path, can be overridden

    # List of heuristic functions to apply during the analysis phase
    # The orchestrator will dynamically import these.
    "ACTIVE_HEURISTICS": [
        "qna_orchestrator.qna_heuristics.heuristics.spacing.analyze_vertical_break",
        "qna_orchestrator.qna_heuristics.heuristics.patterns.analyze_question_number",
        "qna_orchestrator.qna_heuristics.heuristics.patterns.analyze_option_letter",
        "qna_orchestrator.qna_heuristics.heuristics.patterns.analyze_answer_marker",
        "qna_orchestrator.qna_heuristics.heuristics.patterns.analyze_descriptive_question_start",
        "qna_orchestrator.qna_heuristics.heuristics.patterns.analyze_explanation_start",
        "qna_orchestrator.qna_heuristics.heuristics.layout.analyze_indentation",
        "qna_orchestrator.qna_heuristics.heuristics.layout.analyze_font_style",
    ],

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
            "REGEX_QUESTION": r'^\s*(\d+)\.',
            "REGEX_OPTION": r'^\s*\(([a-zA-Z])\)',
            "REGEX_ANSWER": r'^\s*Ans:\s*\(?([a-d])\)?',
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