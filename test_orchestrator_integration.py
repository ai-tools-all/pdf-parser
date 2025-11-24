"""
Test script for Orchestrator integration with ComposableParser.

This verifies that:
1. Orchestrator works with default parser (backward compatibility)
2. Orchestrator accepts custom parsers
3. End-to-end MCQ extraction works
"""

from qna_orchestrator.qna_heuristics.config import get_config
from qna_orchestrator.qna_heuristics.orchestrator import Orchestrator
from qna_orchestrator.qna_heuristics.parser_factory import ParserFactory


def test_default_orchestrator():
    """Test orchestrator with default configuration."""
    print("=" * 70)
    print("Test 1: Orchestrator with Default Parser")
    print("=" * 70)
    
    config = get_config()
    pdf_path = config.get("PDF_PATH", "./data_dir/document.pdf")
    
    # Create orchestrator (uses default parser internally)
    orchestrator = Orchestrator()
    
    print(f"\nParser type: {type(orchestrator.parser).__name__}")
    print(f"Processing: {pdf_path}\n")
    
    try:
        mcqs = orchestrator.run(pdf_path)
        
        print(f"\n✓ Successfully extracted {len(mcqs)} MCQs")
        
        # Show sample MCQs
        for i, mcq in enumerate(mcqs[:3]):
            print(f"\nMCQ {i+1}:")
            print(f"  Q{mcq.question_number}: {mcq.question_text[:80]}...")
            print(f"  Options: {list(mcq.options.keys())}")
            print(f"  Answer: {mcq.answer}")
        
        if len(mcqs) > 3:
            print(f"\n... and {len(mcqs) - 3} more MCQs")
        
        return True
    except FileNotFoundError:
        print(f"✗ PDF file not found: {pdf_path}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_custom_parser_orchestrator():
    """Test orchestrator with custom parser."""
    print("\n" + "=" * 70)
    print("Test 2: Orchestrator with Custom Parser")
    print("=" * 70)
    
    config = get_config()
    pdf_path = config.get("PDF_PATH", "./data_dir/document.pdf")
    
    # Create custom parser using factory
    custom_parser = ParserFactory.create_default(config)
    
    # Create orchestrator with custom parser
    orchestrator = Orchestrator(parser=custom_parser)
    
    print(f"\nParser type: {type(orchestrator.parser).__name__}")
    print(f"Processing: {pdf_path}\n")
    
    try:
        mcqs = orchestrator.run(pdf_path)
        
        print(f"\n✓ Successfully extracted {len(mcqs)} MCQs with custom parser")
        return True
    except FileNotFoundError:
        print(f"✗ PDF file not found: {pdf_path}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all integration tests."""
    results = []
    
    # Test 1: Default orchestrator
    results.append(("Default Parser", test_default_orchestrator()))
    
    # Test 2: Custom parser
    results.append(("Custom Parser", test_custom_parser_orchestrator()))
    
    # Summary
    print("\n" + "=" * 70)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 70)
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    print("\n" + ("✓ All tests PASSED" if all_passed else "✗ Some tests FAILED"))
    print("=" * 70)
    
    return all_passed


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
