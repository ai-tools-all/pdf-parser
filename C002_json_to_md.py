import json
import os
from typing import Dict, List, Tuple, Optional

# Define dataclasses (though not strictly necessary for this script, it helps
# in understanding the structure of the data being processed if you were to
# load it into these objects)
class TextBlock:
    text: str
    bbox: Tuple[float, float, float, float]
    font_size: float
    font_name: str
    type: str

class PageLayout:
    page_number: int
    header: str
    footer: str
    left_column: str
    right_column: str
    page_width: float
    page_height: float
    column_separator_position: Optional[float]
    metadata: Dict

def json_to_markdown(json_input_path: str, markdown_output_path: str):
    """
    Reads layout data from a JSON file and converts it into a Markdown document.

    Args:
        json_input_path (str): Path to the input JSON file containing page layouts.
        markdown_output_path (str): Path where the output Markdown file will be saved.
    """
    try:
        with open(json_input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: JSON input file not found at {json_input_path}")
        print("Please ensure 'extracted_layout_document_layoutlm.json' exists in your 'data_dir'.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {json_input_path}. Check file format.")
        return

    markdown_content = []
    pages = data.get('pages', [])

    for page_layout in pages:
        page_number = page_layout.get('page_number', 'N/A')
        header = page_layout.get('header', '').strip()
        footer = page_layout.get('footer', '').strip()
        left_column = page_layout.get('left_column', '').strip()
        right_column = page_layout.get('right_column', '').strip()

        # Add clear markers for each page
        markdown_content.append(f"---\n\n# Page {page_number}\n")
        markdown_content.append(f"--- Page {page_number} Start ---")

        # Header
        markdown_content.append("## Header")
        markdown_content.append(header)
        markdown_content.append("\n") # Blank line for spacing after header content

        # Main Content (Left and Right Columns)
        markdown_content.append(f"### Page {page_number} Content")
        
        combined_columns_text = []
        # Append left column content if it exists
        if left_column:
            combined_columns_text.append(left_column)
        # Append right column content if it exists
        if right_column:
            combined_columns_text.append(right_column)
        
        # Join the column texts. Using two newlines to separate distinct blocks/paragraphs
        # originating from different columns, ensuring flow from left to right.
        markdown_content.append("\n\n".join(combined_columns_text))
        markdown_content.append("\n") # Blank line for spacing after main content

        # Footer
        markdown_content.append(f"--- Page {page_number} Footer ---")
        markdown_content.append("## Footer")
        markdown_content.append(footer)
        markdown_content.append("\n") # Add a blank line for separation before next page

    # Ensure the output directory exists
    output_dir = os.path.dirname(markdown_output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Write the combined Markdown content to the output file
    with open(markdown_output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(markdown_content))

    print(f"Successfully converted JSON to Markdown at {markdown_output_path}")

if __name__ == "__main__":
    # Define the input JSON file path and output Markdown file path
    json_input_file = "data_dir/003_extracted_layout.json"
    markdown_output_file = "data_dir/003_document_layout.md"
    
    # Call the function to perform the conversion
    json_to_markdown(json_input_file, markdown_output_file)