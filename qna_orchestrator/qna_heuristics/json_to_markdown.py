#!/usr/bin/env python3
"""
Convert MCQ JSON file to readable markdown format

Usage:
    uv run json_to_markdown.py                           # Uses default input, creates output/03_final_mcqs.md
    uv run json_to_markdown.py -i path/to/file.json      # Creates path/to/file.md
    uv run json_to_markdown.py -i input.json -o custom_output.md
"""

import json
import sys
import argparse
from pathlib import Path

def convert_json_to_markdown(json_file_path, output_file_path):
    """Convert MCQ JSON to markdown format"""
    
    # Read JSON file
    with open(json_file_path, 'r', encoding='utf-8') as f:
        mcqs = json.load(f)
    
    # Create markdown content
    markdown_content = []
    markdown_content.append("# MCQ Questions\n")
    markdown_content.append(f"Total Questions: {len(mcqs)}\n")
    markdown_content.append("---\n")
    
    for mcq in mcqs:
        # Question header
        markdown_content.append(f"## Question {mcq['question_number']}\n")
        
        # Question text
        markdown_content.append(f"**Question:** {mcq['question_text']}\n")
        
        # Options
        if mcq.get('options'):
            markdown_content.append("**Options:**")
            for key, value in mcq['options'].items():
                markdown_content.append(f"- {key.upper()}) {value}")
            markdown_content.append("")
        
        # Answer
        if mcq.get('answer'):
            markdown_content.append(f"**Answer:** {mcq['answer'].upper()}\n")
        else:
            markdown_content.append("**Answer:** Not provided\n")
        
        # Explanation
        if mcq.get('explanation'):
            markdown_content.append(f"**Explanation:** {mcq['explanation']}\n")
        else:
            markdown_content.append("**Explanation:** Not provided\n")
        
        markdown_content.append("---\n")
    
    # Write to markdown file
    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(markdown_content))
    
    print(f"Converted {len(mcqs)} questions to markdown: {output_file_path}")

def main():
    parser = argparse.ArgumentParser(description="Convert MCQ JSON to markdown")
    parser.add_argument("--output", "-o", type=str, 
                        help="Output markdown filename (optional - defaults to input with .md extension)")
    parser.add_argument("--input", "-i", type=str, default="output/03_final_mcqs.json",
                        help="Input JSON file path (default: output/03_final_mcqs.json)")
    
    args = parser.parse_args()
    
    # Define input path
    json_file = Path(args.input)
    
    # Define output path - derive from input if not specified
    if args.output:
        output_file = Path(args.output)
    else:
        output_file = json_file.with_suffix('.md')
    
    # Check if JSON file exists
    if not json_file.exists():
        print(f"Error: JSON file not found at {json_file}")
        sys.exit(1)
    
    # Create output directory if needed
    output_file.parent.mkdir(exist_ok=True)
    
    # Convert
    convert_json_to_markdown(json_file, output_file)

if __name__ == "__main__":
    main()