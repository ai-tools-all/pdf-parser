#!/usr/bin/env python3
"""
Simple test script for qna_orchestrator
Usage: python test_qna.py path/to/your/document.pdf
"""

import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from qna_orchestrator.qna_heuristics.orchestrator import Orchestrator

def test_qna_extraction(pdf_path):
    """Test MCQ extraction on a PDF file."""
    print(f"Testing MCQ extraction on: {pdf_path}")
    print("=" * 50)

    try:
        # Create orchestrator and run extraction
        orchestrator = Orchestrator()
        mcqs = orchestrator.run(pdf_path)

        print(f"✅ Successfully extracted {len(mcqs)} MCQs")
        print()

        # Show first 3 MCQs as examples
        for i, mcq in enumerate(mcqs[:3], 1):
            print(f"MCQ {i}:")
            print(f"  Question: {mcq.question_text[:100]}{'...' if len(mcq.question_text) > 100 else ''}")
            print(f"  Options: {len(mcq.options)} choices")
            for key, value in mcq.options.items():
                print(f"    {key}) {value[:50]}{'...' if len(value) > 50 else ''}")
            print(f"  Answer: {mcq.answer}")
            if mcq.explanation:
                print(f"  Explanation: {mcq.explanation[:100]}{'...' if len(mcq.explanation) > 100 else ''}")
            print()

        if len(mcqs) > 3:
            print(f"... and {len(mcqs) - 3} more MCQs")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main entry point for the test-qna command."""
    if len(sys.argv) != 2:
        print("Usage: test-qna <pdf_path>")
        print("Example: test-qna data_dir/document.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)

    test_qna_extraction(pdf_path)

if __name__ == "__main__":
    main()