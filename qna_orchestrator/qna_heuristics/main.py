# in main.py
import json
import argparse
import os
import sys

# Add project root to sys.path to allow for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from qna_orchestrator.qna_heuristics.orchestrator import Orchestrator
from qna_orchestrator.qna_heuristics.conf import load_config

def main():
    """
    Main entry point for the document processing script.
    Usage: python main.py [path_to_pdf] [--parser parser_name]
    """
    print("--- MCQ Extraction Process Starting ---")

    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Extract MCQs from PDF documents')
    parser.add_argument('pdf_path', nargs='?', help='Path to PDF file')
    parser.add_argument('--profile', default='default',
                        help='Configuration profile (e.g., vision_ias, forum_ias)')

    args = parser.parse_args()

    # 1. Load the specific configuration
    config = load_config(args.profile)

    # 2. Inject PDF path if provided
    if args.pdf_path:
        config["PDF_PATH"] = args.pdf_path

    # 3. Initialize Orchestrator with the loaded config
    orchestrator = Orchestrator(full_config=config)

    pdf_path = config.get("PDF_PATH", "./data_dir/document.pdf")
    print(f"Using PDF path: {pdf_path}")
    print(f"Using profile: {args.profile}")

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