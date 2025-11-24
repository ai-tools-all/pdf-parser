# Specific settings for ForumIAS Solutions

PROFILE = {
    "DEFAULT_PARSER": "forum_ias_solutions",
    "ASSEMBLY_STRATEGY": "forum_solutions",

    "PARSERS": {
        "forum_ias_solutions": {
            "type": "heuristic_based",
            "SKIP_PAGES": [],
        }
    },

    "NOISE_PATTERNS": [
        "PTS 2025",
        "SFG 2025",
        "Test Code:",
        "Forum Learning Centre",
        "ForumIAS Academy",
        "https://academy.forumias.com",
        "helpdesk@forumias.academy",
        "admissions@forumias.academy",
        "Page",
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
            # Header: "Q.1)" or "Q.100)"
            "REGEX_SOLUTION_HEADER": r'^\s*Q\.?\s*(\d{1,3})\)',
            # Answer: "Ans) d" or "Ans) a"
            "REGEX_ANSWER_LINE": r'^\s*Ans\)\s*([a-d])',
            # Explanation Start: "Exp)"
            "REGEX_EXPLANATION_START": r'^\s*Exp\)',
            # Optional: Metadata markers to identify end of explanation
            "REGEX_METADATA": r'(Source:\)|Subject:\)|Topic:\)|Subtopic:\))'
        }
    }
}
