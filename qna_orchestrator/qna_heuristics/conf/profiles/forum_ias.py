# Specific settings for ForumIAS

PROFILE = {
    "SKIP_PAGES": [], # Maybe they don't have a cover page

    "NOISE_PATTERNS": [
        "ForumIAS Academy",
        "SFG 2025",
        "Page" # If they put "Page 1" in body text
    ],

    # Forum might use "Q.1)" instead of "1."
    "HEURISTICS": {
        "PATTERNS": {
            "REGEX_QUESTION": r'^\s*Q\.?(\d+)\)',
        }
    }
}