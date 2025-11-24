# Specific settings for VisionIAS

PROFILE = {
    "SKIP_PAGES": [0], # Skip cover page

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

    # VisionIAS needs the clustering heuristic to run FIRST
    "ACTIVE_HEURISTICS": [
        "qna_orchestrator.qna_heuristics.heuristics.clustering.detect_cluster_break",
        "qna_orchestrator.qna_heuristics.heuristics.patterns.detect_question_start_enhanced",
        "qna_orchestrator.qna_heuristics.heuristics.patterns.classify_content_type",
        "qna_orchestrator.qna_heuristics.heuristics.layout.sequence_column_content",
    ],

    "HEURISTICS": {
        "PATTERNS": {
            # Vision numbers can go up to 100, usually strict "1." format
            "REGEX_QUESTION": r'^\s*(\d{1,3})\.',
        }
    }
}