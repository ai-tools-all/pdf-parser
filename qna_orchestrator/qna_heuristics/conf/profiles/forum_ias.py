# Specific settings for ForumIAS

PROFILE = {
    "DEFAULT_PARSER": "forum_ias_parser",
    "ASSEMBLY_STRATEGY": "forum_gatekeeper",

    "PARSERS": {
        "forum_ias_parser": {
            "type": "heuristic_based",
            "SKIP_PAGES": [],  # Forum content often starts on Page 1
        }
    },

    "NOISE_PATTERNS": [
        "Forum Learning Centre",
        "ForumIAS Academy",
        "PTS 2025",
        "SFG 2025",
        "Test Code:",
        "https://academy.forumias.com",
        "helpdesk@forumias.academy",
        "admissions@forumias.academy",
        "Page",  # Removes "Page 2" footer
        "@iasvault",
        "@KingMaker",
        "ForumIAS"
    ],

    "ACTIVE_HEURISTICS": [
        "qna_orchestrator.qna_heuristics.heuristics.patterns.detect_question_start_enhanced",
        "qna_orchestrator.qna_heuristics.heuristics.patterns.classify_content_type",
    ],

    "HEURISTICS": {
        "PATTERNS": {
            # Matches "Q.1)", "Q 1)", "Q. 1)", "Q.100)"
            # Group 1 captures the number
            "REGEX_QUESTION": r'^\s*Q\s*\.?\s*(\d{1,3})\)',
            # Matches "a)", "b)", "(a)", "(b)"
            # Captures the letter in Group 1
            "REGEX_OPTION": r'^\s*\(?([a-d])\)'
        },
        # Forum allows a slightly larger gap tolerance for missing questions
        "MAX_GAP_TOLERANCE": 10
    }
}