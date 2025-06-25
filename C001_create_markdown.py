import json

def create_markdown_from_json(json_file_path, markdown_file_path):
    """
    Reads extracted document layout data from a JSON file and creates a Markdown document.

    Args:
        json_file_path (str): The path to the input JSON file.
        markdown_file_path (str): The path to the output Markdown file.
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: The file {json_file_path} was not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: The file {json_file_path} is not a valid JSON file.")
        return

    markdown_content = []

    for page in data.get('pages', []):
        page_number = page.get('page_number')
        header = page.get('header', '')
        footer = page.get('footer', '')
        left_column = page.get('left_column', '')
        right_column = page.get('right_column', '')

        markdown_content.append(f"<!-- Page {page_number} -->")
        markdown_content.append("\n---\n")

        if header:
            markdown_content.append("**Header:**\n")
            markdown_content.append(header)
            markdown_content.append("\n")

        if left_column:
            markdown_content.append(left_column)
            markdown_content.append("\n")

        if right_column:
            markdown_content.append(right_column)
            markdown_content.append("\n")

        if footer:
            markdown_content.append("**Footer:**\n")
            markdown_content.append(footer)
            markdown_content.append("\n")

    with open(markdown_file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(markdown_content))

    print(f"Markdown document created at {markdown_file_path}")

if __name__ == '__main__':
    json_input_path = './data_dir/extracted_layout_document.json'
    markdown_output_path = './output.md'
    create_markdown_from_json(json_input_path, markdown_output_path)
