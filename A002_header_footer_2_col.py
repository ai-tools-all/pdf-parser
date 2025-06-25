import fitz  # PyMuPDF
import json
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict

@dataclass
class TextBlock:
    text: str
    bbox: Tuple[float, float, float, float]  # x0, y0, x1, y1
    font_size: float
    font_name: str

@dataclass
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

class PDFColumnExtractor:
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
    
    def classify_text_regions(self, text_blocks: List[TextBlock], page_height: float, 
                            separator_x: float) -> Dict[str, List[TextBlock]]:
        """Classify text blocks into header, footer, left column, right column"""
        # Determine header and footer regions based on vertical line extent
        # For now, use top 15% as header and bottom 10% as footer
        header_threshold = page_height * 0.15
        footer_threshold = page_height * 0.9
        
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
            
            # Classify by vertical position first
            if center_y < header_threshold:
                regions['header'].append(block)
            elif center_y > footer_threshold:
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
            regions = self.classify_text_regions(text_blocks, page_rect.height, separator_x)
            
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
    output_path = "./data_dir/extracted_layout_document.json"
    
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
                print(f"  Footer: {len(layout.footer)} chars") 
                print(f"  Left Column: {len(layout.left_column)} chars")
                print(f"  Right Column: {len(layout.right_column)} chars")
                if layout.column_separator_position:
                    print(f"  Column separator at: {layout.column_separator_position:.1f}")
        
        # Example: Print first page's content preview
        if layouts and 'error' not in layouts[0].metadata:
            print(f"\n--- First page content preview ---")
            if layouts[0].header:
                print(f"Header: {layouts[0].header[:100]}{'...' if len(layouts[0].header) > 100 else ''}")
            if layouts[0].left_column:
                print(f"Left Column: {layouts[0].left_column[:200]}{'...' if len(layouts[0].left_column) > 200 else ''}")
            if layouts[0].right_column:
                print(f"Right Column: {layouts[0].right_column[:200]}{'...' if len(layouts[0].right_column) > 200 else ''}")
            if layouts[0].footer:
                print(f"Footer: {layouts[0].footer[:100]}{'...' if len(layouts[0].footer) > 100 else ''}")
        
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