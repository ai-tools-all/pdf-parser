# in main.py
import json
import argparse
import os
import sys

# Add project root to sys.path to allow for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from qna_orchestrator.qna_heuristics.orchestrator import Orchestrator
# from qna_orchestrator.qna_heuristics.config import get_config

def main():
    """
    Main entry point for the document processing script.
    Usage: python main.py [path_to_pdf]
    """
    print("--- MCQ Extraction Process Starting ---")

    # The Orchestrator loads its default config, including the default PDF path.
    # We can override it with a command-line argument.
    orchestrator = Orchestrator()

    pdf_path = orchestrator.config.get("PDF_PATH")
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        print(f"Using PDF path from command line: {pdf_path}")
    else:
        print(f"Using default PDF path from config: {pdf_path}")

    try:
        # The run method executes all phases and saves intermediate files
        final_mcqs = orchestrator.run(pdf_path)

        # You can now work with the final_mcqs list of objects
        if final_mcqs:
            print("\n--- Example of First Extracted MCQ ---")
            first_mcq = final_mcqs[0]
            print(f"Q{first_mcq.question_number}: {first_mcq.question_text}")
            for key, val in first_mcq.options.items():
                print(f"  ({key}) {val}")
            print(f"Answer: {first_mcq.answer}")
            if first_mcq.explanation:
                print(f"Explanation: {first_mcq.explanation[:150]}...")
            else:
                print(f"Explanation: {first_mcq.explanation}")
            print("------------------------------------")

    except FileNotFoundError:
        print(f"\nError: PDF file not found at '{pdf_path}'.")
        print("Please check the path in config.py or provide it as a command-line argument.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()