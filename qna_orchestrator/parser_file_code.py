import re
import os
from pathlib import Path

def parse_markdown_project(markdown_content):
    """
    Parse markdown content to extract file/folder structure and code blocks.
    Returns a dictionary with file paths as keys and code content as values.
    """
    project_structure = {}
    
    # Pattern to match <file>path/filename</file> followed by <code>```language code ```</code>
    file_code_pattern = r'<file>\s*(.*?)\s*</file>\s*<code>\s*```(?:\w+)?\s*(.*?)\s*```\s*</code>'
    
    matches = re.findall(file_code_pattern, markdown_content, re.DOTALL)
    
    for filepath, code in matches:
        filepath = filepath.strip()
        code = code.strip()
        project_structure[filepath] = code
    
    return project_structure

def create_project_structure(project_data, base_dir="generated_project"):
    """
    Create the actual files and directories based on parsed project data.
    """
    base_path = Path(base_dir)
    
    # Create base directory if it doesn't exist
    base_path.mkdir(exist_ok=True)
    
    created_files = []
    created_dirs = set()
    
    for filepath, content in project_data.items():
        full_path = base_path / filepath
        
        # Create parent directories if they don't exist
        parent_dir = full_path.parent
        if parent_dir != base_path:
            parent_dir.mkdir(parents=True, exist_ok=True)
            created_dirs.add(str(parent_dir.relative_to(base_path)))
        
        # Write the file content
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            created_files.append(str(full_path.relative_to(base_path)))
            print(f"✓ Created file: {filepath}")
        except Exception as e:
            print(f"✗ Error creating file {filepath}: {e}")
    
    return created_files, list(created_dirs)

def read_markdown_file(filepath):
    """
    Read and return the content of a markdown file.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        return None
    except Exception as e:
        print(f"Error reading file '{filepath}': {e}")
        return None

def main():
    # Get markdown file path from user
    markdown_file = input("Enter the path to your markdown file: ").strip()
    
    if not markdown_file:
        markdown_file = "project.md"  # Default filename
    
    # Read the markdown file
    content = read_markdown_file(markdown_file)
    if content is None:
        return
    
    # Parse the project structure
    project_structure = parse_markdown_project(content)
    
    if not project_structure:
        print("No file/code blocks found in the markdown file.")
        print("Make sure your markdown uses the format:")
        print("<file>path/filename.ext</file>")
        print("<code>```language")
        print("your code here")
        print("```</code>")
        return
    
    # Ask for output directory
    output_dir = input("Enter output directory name (default: 'generated_project'): ").strip()
    if not output_dir:
        output_dir = "generated_project"
    
    print(f"\nFound {len(project_structure)} files to create:")
    for filepath in project_structure.keys():
        print(f"  - {filepath}")
    
    # Confirm before creating
    confirm = input(f"\nCreate project in '{output_dir}'? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("Operation cancelled.")
        return
    
    # Create the project structure
    print(f"\nCreating project in '{output_dir}'...")
    created_files, created_dirs = create_project_structure(project_structure, output_dir)
    
    print(f"\n✅ Project created successfully!")
    print(f"📁 Created {len(created_dirs)} directories")
    print(f"📄 Created {len(created_files)} files")
    print(f"📍 Location: {os.path.abspath(output_dir)}")

# Alternative function to handle additional markdown formats
def parse_extended_markdown_project(markdown_content):
    """
    Extended parser that can handle multiple formats:
    1. <file>filename</file> <code>```code```</code>
    2. ## filename (as headers)
    3. Directory structure from markdown lists
    """
    project_structure = {}
    
    # Original format
    file_code_pattern = r'<file>\s*(.*?)\s*</file>\s*<code>\s*```(?:\w+)?\s*(.*?)\s*```\s*</code>'
    matches = re.findall(file_code_pattern, markdown_content, re.DOTALL)
    
    for filepath, code in matches:
        project_structure[filepath.strip()] = code.strip()
    
    # Header-based format (## filename.ext)
    header_pattern = r'^##\s+([^\n]+\.[a-zA-Z0-9]+)\s*\n```(?:\w+)?\s*\n(.*?)\n```'
    header_matches = re.findall(header_pattern, markdown_content, re.MULTILINE | re.DOTALL)
    
    for filepath, code in header_matches:
        if filepath.strip() not in project_structure:  # Don't override existing
            project_structure[filepath.strip()] = code.strip()
    
    return project_structure

if __name__ == "__main__":
    main()