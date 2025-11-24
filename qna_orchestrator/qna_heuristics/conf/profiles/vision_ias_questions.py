# Specific settings for VisionIAS

PROFILE = {
    "DEFAULT_PARSER": "vision_ias_questions",
    
    # Use Vision Gatekeeper assembly strategy (Option d as gate)
    "ASSEMBLY_STRATEGY": "vision_gatekeeper",
    
    "PARSERS": {
        "vision_ias_questions": {
            "type": "heuristic_based",
            "SKIP_PAGES": [1],  # Skip first page (instructions) - pages are 1-indexed
        }
    },

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
        "GET IT REPLACED",
        "www.upscmaterials.online",
    ],

    # Sequential parser uses basic signals - Assembler does the heavy lifting
    "ACTIVE_HEURISTICS": [
        "qna_orchestrator.qna_heuristics.heuristics.patterns.detect_question_start_enhanced",
        "qna_orchestrator.qna_heuristics.heuristics.patterns.classify_content_type",
    ],

    "HEURISTICS": {
        "PATTERNS": {
            # Vision numbers can go up to 100, usually strict "1." format
            "REGEX_QUESTION": r'^\s*(\d{1,3})\.',
            # Detect options (a), (b), (c), (d)
            "REGEX_OPTION": r'^\s*\(([a-d])\)',
        }
    }
}