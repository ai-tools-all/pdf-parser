import fitz  # PyMuPDF
import json
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict

# Import the standard PageLayout from protocol
from pdf_extractor_protocol import PageLayout

@dataclass
class TextBlock:
    """Internal data structure for text blocks with formatting info."""
    text: str
    bbox: Tuple[float, float, float, float]  # x0, y0, x1, y1
    font_size: float
    font_name: str

class PDFColumnExtractor:
    """
    PDF layout extractor with colored footer detection support.

    Implements the PDFLayoutExtractor protocol for compatibility with
    the testing framework. Specializes in detecting colored footer regions
    and extracting two-column layouts.

    Args:
        pdf_path: Path to the PDF file to process
    """
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        
    def detect_vertical_lines(self, page) -> List[Tuple[float, float, float, float]]:
        """Detect vertical lines in the page that might separate columns"""
        vertical_lines = []
        
        try:
            drawings = page.get_drawings()
            for drawing in drawings:
                if "items" in drawing:
                    for item in drawing["items"]:
                        if len(item) >= 5 and item[0] == "l":  # line with enough coordinates
                            x1, y1, x2, y2 = item[1:5]
                            # Check if it's a vertical line (small horizontal difference, significant vertical difference)
                            if abs(x2 - x1) < 5 and abs(y2 - y1) > 100:
                                vertical_lines.append((x1, y1, x2, y2))
        except Exception as e:
            print(f"Warning: Could not detect vertical lines on page {page.number}: {e}")
        
        # Alternative method: look for vertical lines in vector graphics
        try:
            # Get vector graphics paths
            paths = page.get_cdrawings()
            for path in paths:
                if "items" in path:
                    for item in path["items"]:
                        if item[0] == "l" and len(item) >= 5:  # line
                            x1, y1, x2, y2 = item[1:5]
                            if abs(x2 - x1) < 5 and abs(y2 - y1) > 100:
                                vertical_lines.append((x1, y1, x2, y2))
        except:
            pass  # Some PDFs might not have this method
        
        return vertical_lines
    
    def get_text_blocks(self, page) -> List[TextBlock]:
        """Extract text blocks with their positions and formatting"""
        text_blocks = []
        
        try:
            blocks = page.get_text("dict")
            for block in blocks.get("blocks", []):
                if "lines" in block:
                    for line in block["lines"]:
                        line_text = ""
                        font_size = 0
                        font_name = ""
                        
                        for span in line.get("spans", []):
                            line_text += span.get("text", "")
                            font_size = max(font_size, span.get("size", 0))
                            if not font_name:
                                font_name = span.get("font", "")
                        
                        if line_text.strip():
                            bbox = line.get("bbox", [0, 0, 0, 0])
                            if len(bbox) >= 4:
                                text_blocks.append(TextBlock(
                                    text=line_text.strip(),
                                    bbox=tuple(bbox[:4]),  # Ensure only 4 values
                                    font_size=font_size,
                                    font_name=font_name
                                ))
        except Exception as e:
            print(f"Warning: Error extracting text blocks from page {page.number}: {e}")
            # Fallback to simple text extraction
            try:
                text = page.get_text()
                if text.strip():
                    page_rect = page.rect
                    text_blocks.append(TextBlock(
                        text=text.strip(),
                        bbox=(page_rect.x0, page_rect.y0, page_rect.x1, page_rect.y1),
                        font_size=12.0,  # Default font size
                        font_name="Unknown"
                    ))
            except:
                pass
        
        return text_blocks
    
    def find_column_separator(self, page, text_blocks: List[TextBlock]) -> Optional[float]:
        """Find the column separator position"""
        page_rect = page.rect
        page_width = page_rect.width
        
        # First, try to find vertical lines
        vertical_lines = self.detect_vertical_lines(page)
        if vertical_lines:
            # Find the longest vertical line near the center
            center_x = page_width / 2
            best_line = None
            best_length = 0
            
            for line in vertical_lines:
                x1, y1, x2, y2 = line
                length = abs(y2 - y1)
                distance_from_center = abs((x1 + x2) / 2 - center_x)
                
                if distance_from_center < page_width * 0.3 and length > best_length:
                    best_line = line
                    best_length = length
            
            if best_line:
                return (best_line[0] + best_line[2]) / 2
        
        # If no vertical lines found, analyze text distribution
        if not text_blocks:
            return page_width / 2
            
        # Group text blocks by their x-position
        left_blocks = []
        right_blocks = []
        
        # Try different separator positions and find the best one
        for separator_x in range(int(page_width * 0.3), int(page_width * 0.7), 10):
            left_count = sum(1 for block in text_blocks if block.bbox[2] < separator_x)
            right_count = sum(1 for block in text_blocks if block.bbox[0] > separator_x)
            
            if left_count > 0 and right_count > 0:
                return float(separator_x)
        
        return page_width / 2
    
    def detect_colored_backgrounds(self, page) -> List[Tuple[float, float, float, float]]:
        """Detect rectangles with colored backgrounds that might indicate footers"""
        colored_regions = []
        
        try:
            # Get all drawings/shapes on the page
            drawings = page.get_drawings()
            for drawing in drawings:
                if "items" in drawing and "fill" in drawing:
                    # Check if this drawing has a fill color (background)
                    fill_color = drawing.get("fill")
                    if fill_color and fill_color != [1.0, 1.0, 1.0]:  # Not white background
                        # Extract rectangle bounds from the drawing
                        if "rect" in drawing:
                            rect = drawing["rect"]
                            if len(rect) >= 4:
                                colored_regions.append(tuple(rect[:4]))
        except Exception as e:
            print(f"Warning: Could not detect colored backgrounds on page {page.number}: {e}")
        
        return colored_regions
    
    def classify_text_regions(self, page, text_blocks: List[TextBlock], page_height: float, 
                            separator_x: float) -> Dict[str, List[TextBlock]]:
        """Classify text blocks into header, footer, left column, right column"""
        # Determine header region - top 15% of page
        header_threshold = page_height * 0.15
        
        # Detect colored backgrounds that might indicate footers
        colored_regions = self.detect_colored_backgrounds(page)
        footer_regions = []
        
        # Look for colored regions in the bottom half of the page
        for region in colored_regions:
            x0, y0, x1, y1 = region
            if y0 > page_height * 0.5:  # Bottom half of page
                footer_regions.append(region)
        
        # If no colored footer regions found, use conservative bottom 5% threshold
        # Only if there's text there and it looks like footer content
        footer_threshold = page_height * 0.95
        potential_footer_blocks = [block for block in text_blocks 
                                 if (block.bbox[1] + block.bbox[3]) / 2 > footer_threshold]
        
        # Check if potential footer blocks look like actual footers
        has_footer = False
        if potential_footer_blocks:
            footer_text = " ".join([block.text for block in potential_footer_blocks]).lower()
            # Common footer indicators
            footer_indicators = ['page', 'copyright', '©', '®', 'www.', '.com', '.org', 
                               'all rights reserved', 'confidential']
            if any(indicator in footer_text for indicator in footer_indicators):
                has_footer = True
            # Also check if it's very short text (likely page numbers)
            elif len(footer_text.strip()) < 50 and any(char.isdigit() for char in footer_text):
                has_footer = True
        
        regions = {
            'header': [],
            'footer': [],
            'left_column': [],
            'right_column': []
        }
        
        for block in text_blocks:
            x0, y0, x1, y1 = block.bbox
            center_y = (y0 + y1) / 2
            center_x = (x0 + x1) / 2
            
            # Check if block is in a colored footer region
            in_colored_footer = False
            for footer_region in footer_regions:
                fx0, fy0, fx1, fy1 = footer_region
                if (x0 >= fx0 and x1 <= fx1 and y0 >= fy0 and y1 <= fy1):
                    in_colored_footer = True
                    break
            
            # Classify by vertical position and footer detection
            if center_y < header_threshold:
                regions['header'].append(block)
            elif in_colored_footer or (has_footer and center_y > footer_threshold):
                regions['footer'].append(block)
            else:
                # Classify by horizontal position for main content
                if center_x < separator_x:
                    regions['left_column'].append(block)
                else:
                    regions['right_column'].append(block)
        
        return regions
    
    def blocks_to_text(self, blocks: List[TextBlock]) -> str:
        """Convert text blocks to continuous text"""
        if not blocks:
            return ""
        
        # Sort blocks by position (top to bottom, left to right)
        sorted_blocks = sorted(blocks, key=lambda b: (b.bbox[1], b.bbox[0]))
        
        # Group blocks into lines based on y-position
        lines = []
        current_line = []
        current_y = None
        
        for block in sorted_blocks:
            block_y = (block.bbox[1] + block.bbox[3]) / 2
            
            if current_y is None or abs(block_y - current_y) < 10:
                current_line.append(block)
                current_y = block_y
            else:
                if current_line:
                    lines.append(current_line)
                current_line = [block]
                current_y = block_y
        
        if current_line:
            lines.append(current_line)
        
        # Convert lines to text
        text_lines = []
        for line in lines:
            line_text = " ".join(block.text for block in sorted(line, key=lambda b: b.bbox[0]))
            text_lines.append(line_text)
        
        return "\n".join(text_lines)
    
    def extract_page_layout(self, page_num: int) -> PageLayout:
        """Extract layout information from a single page"""
        try:
            page = self.doc[page_num]
            page_rect = page.rect
            
            # Get text blocks
            text_blocks = self.get_text_blocks(page)
            
            # Find column separator
            separator_x = self.find_column_separator(page, text_blocks)
            
            # Classify text regions
            regions = self.classify_text_regions(page, text_blocks, page_rect.height, separator_x)
            
            # Convert regions to text
            header_text = self.blocks_to_text(regions['header'])
            footer_text = self.blocks_to_text(regions['footer'])
            left_column_text = self.blocks_to_text(regions['left_column'])
            right_column_text = self.blocks_to_text(regions['right_column'])
            
            # Gather metadata
            metadata = {
                'total_text_blocks': len(text_blocks),
                'header_blocks': len(regions['header']),
                'footer_blocks': len(regions['footer']),
                'left_column_blocks': len(regions['left_column']),
                'right_column_blocks': len(regions['right_column']),
                'vertical_lines_detected': len(self.detect_vertical_lines(page)),
                'colored_footer_regions': len(self.detect_colored_backgrounds(page)),
                'has_footer': len(regions['footer']) > 0,
                'page_rect': [page_rect.x0, page_rect.y0, page_rect.x1, page_rect.y1]
            }
            
            return PageLayout(
                page_number=page_num + 1,
                header=header_text,
                footer=footer_text,
                left_column=left_column_text,
                right_column=right_column_text,
                page_width=page_rect.width,
                page_height=page_rect.height,
                column_separator_position=separator_x,
                metadata=metadata
            )
            
        except Exception as e:
            print(f"Error processing page {page_num + 1}: {e}")
            # Return a minimal layout with error info
            return PageLayout(
                page_number=page_num + 1,
                header="",
                footer="",
                left_column="",
                right_column="",
                page_width=0.0,
                page_height=0.0,
                column_separator_position=None,
                metadata={'error': str(e)}
            )
    
    def extract_all_pages(self) -> List[PageLayout]:
        """Extract layout information from all pages"""
        layouts = []
        for page_num in range(len(self.doc)):
            layout = self.extract_page_layout(page_num)
            layouts.append(layout)
        return layouts
    
    def save_to_json(self, output_path: str, layouts: List[PageLayout]):
        """Save extracted layouts to JSON file"""
        data = {
            'pdf_path': self.pdf_path,
            'total_pages': len(layouts),
            'pages': [asdict(layout) for layout in layouts]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def close(self):
        """Close the PDF document"""
        self.doc.close()

def main():
    # Example usage
    pdf_path = "./data_dir/document.pdf"  # Replace with your PDF path
    output_path = "./data_dir/003_extracted_layout.json"
    
    # Check if PDF file exists
    import os
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file '{pdf_path}' not found.")
        print("Please update the pdf_path variable with the correct path to your PDF file.")
        return
    
    try:
        print(f"Processing PDF: {pdf_path}")
        extractor = PDFColumnExtractor(pdf_path)
        
        # Extract all pages
        print("Extracting page layouts...")
        layouts = extractor.extract_all_pages()
        
        # Save to JSON
        extractor.save_to_json(output_path, layouts)
        
        # Print summary
        print(f"\nProcessed {len(layouts)} pages")
        for i, layout in enumerate(layouts):
            if 'error' in layout.metadata:
                print(f"\nPage {layout.page_number}: ERROR - {layout.metadata['error']}")
            else:
                print(f"\nPage {layout.page_number}:")
                print(f"  Header: {len(layout.header)} chars")
                if layout.metadata.get('has_footer', False):
                    print(f"  Footer: {len(layout.footer)} chars")
                else:
                    print(f"  Footer: None detected")
                print(f"  Left Column: {len(layout.left_column)} chars")
                print(f"  Right Column: {len(layout.right_column)} chars")
                if layout.column_separator_position:
                    print(f"  Column separator at: {layout.column_separator_position:.1f}")
                if layout.metadata.get('colored_footer_regions', 0) > 0:
                    print(f"  Colored footer regions: {layout.metadata['colored_footer_regions']}")
        
        # Example: Print first page's content preview
        if layouts and 'error' not in layouts[0].metadata:
            print(f"\n--- First page content preview ---")
            if layouts[0].header:
                print(f"Header: {layouts[0].header[:100]}{'...' if len(layouts[0].header) > 100 else ''}")
            if layouts[0].left_column:
                print(f"Left Column: {layouts[0].left_column[:200]}{'...' if len(layouts[0].left_column) > 200 else ''}")
            if layouts[0].right_column:
                print(f"Right Column: {layouts[0].right_column[:200]}{'...' if len(layouts[0].right_column) > 200 else ''}")
            if layouts[0].footer and layouts[0].metadata.get('has_footer', False):
                print(f"Footer: {layouts[0].footer[:100]}{'...' if len(layouts[0].footer) > 100 else ''}")
            elif not layouts[0].metadata.get('has_footer', False):
                print("Footer: None detected")
        
        extractor.close()
        print(f"\nResults saved to {output_path}")
        
    except FileNotFoundError:
        print(f"Error: Could not find PDF file '{pdf_path}'")
    except Exception as e:
        print(f"Error processing PDF: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()