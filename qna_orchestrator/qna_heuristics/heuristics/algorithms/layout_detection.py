import json
from typing import List, Dict, Any, Optional
# Assuming TextBlock, Page, and Document are defined in data_models.py
from qna_orchestrator.qna_heuristics.data_models import TextBlock, Page, Document

def detect_column(block: TextBlock, column_separator_x: float) -> str:
    """
    Determines if a text block belongs to the left or right column based on its bbox.
    """
    # Use the horizontal center of the block for classification
    block_center_x = (block.bbox[0] + block.bbox[2]) / 2
    if block_center_x < column_separator_x:
        return "left_column"
    else:
        return "right_column"

def calculate_column_separator(page_width: float, left_blocks: List[TextBlock], right_blocks: List[TextBlock]) -> float:
    """
    Calculates an approximate column separator X-coordinate based on the given blocks.
    If blocks are available, it uses the average of the max x of left blocks and min x of right blocks.
    Otherwise, it defaults to the page midpoint.
    """
    max_left_x = 0.0
    if left_blocks:
        max_left_x = max(b.bbox[2] for b in left_blocks)

    min_right_x = page_width
    if right_blocks:
        min_right_x = min(b.bbox[0] for b in right_blocks)
    
    if left_blocks and right_blocks:
        # If both columns have blocks, the separator is likely between the rightmost left block
        # and the leftmost right block. Take their midpoint.
        return (max_left_x + min_right_x) / 2
    elif left_blocks:
        # If only left blocks, assume separator is slightly to the right of the rightmost left block
        # This is a heuristic, adjust as needed based on typical document layouts
        return max_left_x + 20 
    elif right_blocks:
        # If only right blocks, assume separator is slightly to the left of the leftmost right block
        # This is a heuristic, adjust as needed based on typical document layouts
        return min_right_x - 20 
    else:
        # Fallback to page midpoint if no blocks are provided
        return page_width / 2

if __name__ == "__main__":
    # This part demonstrates how to use the algorithm with sample.json
    sample_json_path = "./sample.json"
    
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
            
            # Calculate the column separator for the first page
            separator_x = calculate_column_separator(
                first_page.page_width,
                first_page.left_column_blocks,
                first_page.right_column_blocks
            )
            print(f"Calculated column separator X for page {first_page.page_number}: {separator_x:.2f}")

            all_blocks_on_page = (
                first_page.left_column_blocks +
                first_page.right_column_blocks +
                first_page.other_blocks
            )
            
            # Sort blocks by their y-coordinate for a more natural reading order in output
            all_blocks_on_page.sort(key=lambda b: b.bbox[1])

            print("\n--- Column Detection Results ---")
            for block in all_blocks_on_page:
                detected_col = detect_column(block, separator_x)
                print(f"Block ID: {block.id}, Text: '{block.text[:50]}...', Detected Column: {detected_col}")
        else:
            print("No pages found in sample.json.")

    except FileNotFoundError:
        print(f"Error: {sample_json_path} not found. Please ensure the file exists.")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {sample_json_path}. Check file format.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
