"""
Test script for ComposableParser with default strategies.

This script verifies that the new composable parser architecture works
correctly by parsing a sample PDF and comparing results.
"""

from qna_orchestrator.qna_heuristics.config import get_config
from qna_orchestrator.qna_heuristics.composable_parser import ComposableParser
from qna_orchestrator.qna_heuristics.strategies.implementations import (
    PyMuPDFExtractor,
    TwoColumnLayoutDetector,
    DefaultHeuristicAnalyzer
)


def test_composable_parser():
    """Test the ComposableParser with default strategies."""
    
    # Load config
    config = get_config()
    
    # Create parser with strategies
    parser = ComposableParser(
        extraction_strategy=PyMuPDFExtractor(config),
        layout_strategy=TwoColumnLayoutDetector(config),
        analysis_strategy=DefaultHeuristicAnalyzer(config),
        config=config
    )
    
    print("=" * 60)
    print("Testing ComposableParser")
    print("=" * 60)
    print(f"\nParser configuration:")
    print(parser)
    print()
    
    # Get PDF path from config
    pdf_path = config.get("PDF_PATH", "./data_dir/document.pdf")
    
    print(f"Parsing PDF: {pdf_path}")
    print("-" * 60)
    
    try:
        # Parse the document
        document = parser.parse(pdf_path)
        
        print(f"✓ Successfully parsed {len(document.pages)} pages")
        print()
        
        # Display summary for each page
        for page in document.pages[:3]:  # Show first 3 pages
            print(f"Page {page.page_number}:")
            print(f"  Dimensions: {page.page_width:.1f} x {page.page_height:.1f} pts")
            print(f"  Left column blocks: {len(page.left_column_blocks)}")
            print(f"  Right column blocks: {len(page.right_column_blocks)}")
            print(f"  Other blocks (header/footer): {len(page.other_blocks)}")
            
            # Show sample analysis results
            analyzed_blocks = [b for b in page.left_column_blocks + page.right_column_blocks 
                             if b.analysis_results]
            print(f"  Blocks with analysis: {len(analyzed_blocks)}")
            
            if analyzed_blocks:
                sample = analyzed_blocks[0]
                print(f"  Sample analysis: {sample.analysis_results[:2]}")
            print()
        
        if len(document.pages) > 3:
            print(f"... and {len(document.pages) - 3} more pages")
        
        print("=" * 60)
        print("✓ ComposableParser test PASSED")
        print("=" * 60)
        
        return document
        
    except FileNotFoundError:
        print(f"✗ PDF file not found: {pdf_path}")
        print("\nPlease ensure you have a PDF at the configured path,")
        print("or update PDF_PATH in config.py")
        return None
    except Exception as e:
        print(f"✗ Error during parsing: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    test_composable_parser()
