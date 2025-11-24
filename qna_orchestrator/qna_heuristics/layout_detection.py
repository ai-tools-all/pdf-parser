import json

def get_horizontal_distance(box1, box2):
    """Calculate the horizontal distance between two bounding boxes."""
    x1_min, _, x1_max, _ = box1
    x2_min, _, x2_max, _ = box2
    
    # Check for overlap
    if x1_max < x2_min:
        return x2_min - x1_max
    elif x2_max < x1_min:
        return x1_min - x2_max
    else:
        return 0

def get_vertical_distance(box1, box2):
    """Calculate the vertical distance between two bounding boxes."""
    _, y1_min, _, y1_max = box1
    _, y2_min, _, y2_max = box2
    
    # Check for overlap
    if y1_max < y2_min:
        return y2_min - y1_max
    elif y2_max < y1_min:
        return y1_min - y2_max
    else:
        return 0

def group_blocks_by_layout(blocks, vertical_threshold=20, horizontal_threshold=50):
    """Group blocks based on their spatial layout (columns and paragraphs)."""
    
    if not blocks:
        return []

    # Sort blocks by their vertical position, then horizontal
    blocks.sort(key=lambda b: (b['bbox'][1], b['bbox'][0]))
    
    groups = []
    current_group = [blocks[0]]
    
    for i in range(1, len(blocks)):
        prev_block = blocks[i-1]
        current_block = blocks[i]
        
        v_dist = get_vertical_distance(prev_block['bbox'], current_block['bbox'])
        h_dist = get_horizontal_distance(prev_block['bbox'], current_block['bbox'])
        
        # Check for a large horizontal gap, suggesting a new column
        if h_dist > horizontal_threshold:
            groups.append(current_group)
            current_group = [current_block]
        # Check for a large vertical gap, suggesting a new paragraph
        elif v_dist > vertical_threshold:
            groups.append(current_group)
            current_group = [current_block]
        else:
            current_group.append(current_block)
            
    groups.append(current_group)
    return groups

def analyze_layout(file_path):
    """
    Analyzes the layout of a document from a JSON file.

    Args:
        file_path (str): The path to the JSON file.

    Returns:
        dict: A dictionary containing the structured layout of the document.
    """
    with open(file_path, 'r') as f:
        data = json.load(f)

    structured_layout = {"pages": []}

    for page in data['pages']:
        page_layout = {
            "page_number": page['page_number'],
            "columns": []
        }
        
        all_blocks = page.get('left_column_blocks', []) + \
                     page.get('right_column_blocks', []) + \
                     page.get('other_blocks', [])
        
        if not all_blocks:
            continue

        # Group blocks into columns and paragraphs
        layout_groups = group_blocks_by_layout(all_blocks)
        
        # A simple way to form columns: group the groups by their horizontal position
        columns = {}
        for group in layout_groups:
            # Use the horizontal center of the first block in a group to determine column
            x_center = (group[0]['bbox'][0] + group[0]['bbox'][2]) / 2
            
            # Find which column this group belongs to
            found_column = False
            for col_key in columns:
                # If the x_center is close to the center of a column, add it
                if abs(x_center - col_key) < 100: # 100 is a heuristic for column width
                    columns[col_key].append(group)
                    found_column = True
                    break
            
            if not found_column:
                columns[x_center] = [group]

        # Convert dictionary of columns to a list of columns
        sorted_columns = sorted(columns.items())
        
        for _, groups_in_col in sorted_columns:
            column_content = []
            for group in groups_in_col:
                # Each group is a paragraph
                paragraph_text = " ".join([b['text'] for b in group])
                
                # Simple heading detection based on font size
                is_heading = all(b['font_size'] > 12 for b in group) # Heuristic
                
                paragraph_info = {
                    "type": "heading" if is_heading else "paragraph",
                    "text": paragraph_text,
                    "blocks": group
                }
                column_content.append(paragraph_info)
            
            page_layout['columns'].append(column_content)
            
        structured_layout['pages'].append(page_layout)

    return structured_layout

if __name__ == "__main__":
    layout = analyze_layout('sample.json')
    print(json.dumps(layout, indent=2))
