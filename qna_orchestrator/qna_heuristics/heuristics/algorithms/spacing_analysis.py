import json
from typing import List, Dict, Any, Optional
# Assuming TextBlock, Page, and Document are defined in data_models.py
from qna_orchestrator.qna_heuristics.data_models import TextBlock, Page, Document
import numpy as np

def analyze_line_spacing(blocks: List[TextBlock], config: Dict) -> List[Dict]:
    """
    Analyzes line spacing within a list of text blocks and identifies significant increases.

    Args:
        blocks: A list of TextBlock objects, assumed to be from a single column and sorted.
        config: A dictionary containing configuration parameters, e.g.,
                {"spacing_increase_threshold": 0.10} for 10% increase.

    Returns:
        A list of dictionaries, each describing a detected spacing anomaly.
    """
    anomalies = []
    if len(blocks) < 2:
        return anomalies

    # Sort blocks by their y-coordinate (top of bbox) to ensure correct order
    # Then by x-coordinate for tie-breaking or multi-line blocks starting at same y
    sorted_blocks = sorted(blocks, key=lambda b: (b.bbox[1], b.bbox[0]))

    inter_line_spacings = []
    for i in range(len(sorted_blocks) - 1):
        current_block = sorted_blocks[i]
        next_block = sorted_blocks[i+1]

        # Calculate vertical distance between bottom of current block and top of next block
        spacing = next_block.bbox[1] - current_block.bbox[3]
        
        # Only consider positive spacing (next block is below current)
        # and ignore very small or negative spacings which might indicate
        # multi-line blocks or overlapping text.
        if spacing > 0.1: # A small threshold to filter out noise
            inter_line_spacings.append(spacing)

    if not inter_line_spacings:
        return anomalies

    # Calculate normal/average spacing (using median for robustness against outliers)
    normal_spacing = np.median(inter_line_spacings)
    
    # Get the configured threshold, default to 10% if not specified
    spacing_increase_threshold = config.get("spacing_increase_threshold", 0.10)

    for i in range(len(sorted_blocks) - 1):
        current_block = sorted_blocks[i]
        next_block = sorted_blocks[i+1]
        
        spacing = next_block.bbox[1] - current_block.bbox[3]

        # Check for significant increase
        if spacing > normal_spacing * (1 + spacing_increase_threshold):
            anomalies.append({
                "type": "significant_line_spacing_increase",
                "block_id_1": current_block.id,
                "block_text_1": current_block.text,
                "block_id_2": next_block.id,
                "block_text_2": next_block.text,
                "actual_spacing": spacing,
                "normal_spacing": normal_spacing,
                "increase_percentage": (spacing / normal_spacing - 1) * 100,
                "threshold_percentage": spacing_increase_threshold * 100
            })
    
    return anomalies

if __name__ == "__main__":
    # This part demonstrates how to use the algorithm with sample.json
    sample_json_path = "qna_orchestrator/qna_heuristics/sample.json"
    
    # Configuration for spacing analysis
    analysis_config = {
        "spacing_increase_threshold": 0.10 # 10% increase (can be 0.05 for 5%, etc.)
    }

    try:
        with open(sample_json_path, 'r') as f:
            sample_data = json.load(f)
        
        # Convert raw dicts to TextBlock and Page objects for consistency
        # This assumes TextBlock, Page, Document dataclasses have a constructor
        # that can take keyword arguments matching the JSON keys.
        document_data = Document(
            pdf_path=sample_data["pdf_path"],
            pages=[
                Page(
                    page_number=p["page_number"],
                    page_width=p["page_width"],
                    page_height=p["page_height"],
                    left_column_blocks=[TextBlock(**b) for b in p["left_column_blocks"]],
                    right_column_blocks=[TextBlock(**b) for b in p["right_column_blocks"]],
                    other_blocks=[TextBlock(**b) for b in p["other_blocks"]],
                    raw_left_text=p.get("raw_left_text", ""),
                    raw_right_text=p.get("raw_right_text", "")
                ) for p in sample_data["pages"]
            ]
        )

        if document_data.pages:
            first_page = document_data.pages[0]
            
            print(f"--- Analyzing Line Spacing for Page {first_page.page_number} ---")

            # Analyze left column
            print("\nLeft Column Spacing Anomalies:")
            left_column_anomalies = analyze_line_spacing(first_page.left_column_blocks, analysis_config)
            if left_column_anomalies:
                for anomaly in left_column_anomalies:
                    print(f"  - Detected significant spacing increase between '{anomaly['block_text_1'][:30]}...' and '{anomaly['block_text_2'][:30]}...'")
                    print(f"    Actual: {anomaly['actual_spacing']:.2f}, Normal: {anomaly['normal_spacing']:.2f}, Increase: {anomaly['increase_percentage']:.2f}%")
            else:
                print("  No significant spacing anomalies detected in the left column.")

            # Analyze right column
            print("\nRight Column Spacing Anomalies:")
            right_column_anomalies = analyze_line_spacing(first_page.right_column_blocks, analysis_config)
            if right_column_anomalies:
                for anomaly in right_column_anomalies:
                    print(f"  - Detected significant spacing increase between '{anomaly['block_text_1'][:30]}...' and '{anomaly['block_text_2'][:30]}...'")
                    print(f"    Actual: {anomaly['actual_spacing']:.2f}, Normal: {anomaly['normal_spacing']:.2f}, Increase: {anomaly['increase_percentage']:.2f}%")
            else:
                print("  No significant spacing anomalies detected in the right column.")

        else:
            print("No pages found in sample.json.")

    except FileNotFoundError:
        print(f"Error: {sample_json_path} not found. Please ensure the file exists.")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {sample_json_path}. Check file format.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
