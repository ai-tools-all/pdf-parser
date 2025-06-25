import fitz  # PyMuPDF
import json
import os
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from PIL import Image

# Import layoutparser
import layoutparser as lp
import torch # Make sure torch is imported for device checking

@dataclass
class TextBlock:
    text: str
    bbox: Tuple[float, float, float, float]  # x0, y0, x1, y1
    font_size: float = -1.0  # LayoutLM doesn't directly provide font size, default to -1
    font_name: str = "unknown" # LayoutLM doesn't directly provide font name, default to "unknown"
    type: str = "text" # Semantic type from LayoutLM (e.g., 'Text', 'Title', 'List')

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
        
        # Determine the device to use
        if torch.cuda.is_available():
            print("CUDA is available. Using GPU for LayoutParser.")
            self.device = "cuda"
        else:
            print("CUDA not available. Using CPU for LayoutParser.")
            self.device = "cpu"

        # Initialize LayoutParser model
        # Using PubLayNet pre-trained model for general document layout analysis
        # It can detect Text, Title, List, Table, Figure
        # You might need to download the model weights the first time
        self.layout_model = lp.AutoLayoutModel(
            config_path="lp://PubLayNet/faster_rcnn_R_50_FPN_3x/config",
            extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.8], # Confidence threshold
            device=self.device # Pass the determined device
            # --- THE FIX IS HERE: Removed 'label_map=lp.models.PubLayNet.LABEL_MAP' ---
            # AutoLayoutModel handles label_map automatically based on config_path
        )
        
        # OCR removed - using PDF's native text extraction

    def _render_page_to_image(self, page):
        """Render a PyMuPDF page to a PIL Image."""
        # Render the page at 300 DPI for good quality
        pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        return img

    def get_text_blocks_from_layoutlm(self, page) -> List[TextBlock]:
        """
        Extract text blocks using LayoutParser for layout detection and PDF's native text for content.
        This provides semantic types and robust bounding boxes without OCR.
        """
        image = self._render_page_to_image(page)
        
        # Detect layout elements
        layout = self.layout_model.detect(image)
        
        # Get native PDF text blocks for overlapping with layout regions
        pdf_text_blocks = page.get_text("dict")["blocks"]
        
        text_blocks = []
        for block in layout:
            # Filter for text-like blocks (e.g., 'Text', 'Title', 'List')
            if block.type in ["Text", "Title", "List"]:
                # Get bounding box from layout detection
                layout_bbox = (block.coordinates[0], block.coordinates[1], 
                             block.coordinates[2], block.coordinates[3])
                
                # Find overlapping PDF text blocks and extract text
                block_text = self._extract_text_from_region(page, layout_bbox)
                
                if block_text and block_text.strip():
                    text_blocks.append(TextBlock(
                        text=block_text.strip(),
                        bbox=layout_bbox,
                        font_size=-1.0, # LayoutLM doesn't provide this directly
                        font_name="PDF_native", # Indication of source
                        type=block.type
                    ))
        
        return text_blocks
    
    def _extract_text_from_region(self, page, bbox: Tuple[float, float, float, float]) -> str:
        """Extract text from a specific region of the page using PDF's native text."""
        x0, y0, x1, y1 = bbox
        # Create a rectangle for the region
        rect = fitz.Rect(x0, y0, x1, y1)
        # Extract text from that region
        text = page.get_textbox(rect)
        return text
    
    def detect_vertical_lines(self, page) -> List[Tuple[float, float, float, float]]:
        """Detect vertical lines in the page that might separate columns"""
        drawings = page.get_drawings()
        vertical_lines = []
        page_height = page.rect.height
        
        for drawing in drawings:
            for item in drawing["items"]:
                if item[0] == "l":  # line
                    if len(item) == 5: # 'l' (type) + x0, y0, x1, y1 (4 coords) = 5 elements total
                        x0, y0, x1, y1 = item[1:5]
                        if abs(x1 - x0) < page.rect.width * 0.01 and abs(y1 - y0) > page_height * 0.2:
                            vertical_lines.append((x0, y0, x1, y1))
                    else:
                        print(f"Warning: Malformed line item detected, skipping. Expected 5 elements, got {len(item)}: {item}")
        
        return vertical_lines
    
    def find_column_separator(self, page, text_blocks: List[TextBlock]) -> Tuple[float, Optional[float], Optional[float]]:
        """
        Find the column separator position (X-coordinate) and the Y-coordinates
        of the dominant vertical line if found.
        Returns: (separator_x, line_y0, line_y1)
        """
        page_rect = page.rect
        page_width = page_rect.width
        
        separator_x: float = page_width / 2
        line_y0: Optional[float] = None
        line_y1: Optional[float] = None
        
        # First, try to find vertical lines (from PDF's drawing commands)
        vertical_lines = self.detect_vertical_lines(page)
        if vertical_lines:
            center_x = page_width / 2
            best_line = None
            best_length = 0.0
            
            for line in vertical_lines:
                x0, y0, x1, y1 = line
                length = abs(y1 - y0)
                distance_from_center = abs((x0 + x1) / 2 - center_x)
                
                if distance_from_center < page_width * 0.25 and length > best_length:
                    best_line = line
                    best_length = length
            
            if best_line:
                separator_x = (best_line[0] + best_line[2]) / 2
                line_y0 = best_line[1]
                line_y1 = best_line[3]
                return separator_x, line_y0, line_y1
        
        # If no dominant vertical lines found, analyze text distribution (from LayoutLM blocks)
        if not text_blocks:
            return page_width / 2, None, None
            
        for test_separator_x in range(int(page_width * 0.3), int(page_width * 0.7) + 1, 5):
            left_count = 0
            right_count = 0
            for block in text_blocks:
                block_center_x = (block.bbox[0] + block.bbox[2]) / 2
                if block_center_x < test_separator_x:
                    left_count += 1
                elif block_center_x > test_separator_x:
                    right_count += 1
            
            if left_count > len(text_blocks) * 0.1 and right_count > len(text_blocks) * 0.1:
                separator_x = float(test_separator_x)
                break
        
        return separator_x, None, None
    
    def classify_text_regions(self, text_blocks: List[TextBlock], page_height: float, 
                            separator_x: float, header_y_max: Optional[float], footer_y_min: Optional[float]) -> Dict[str, List[TextBlock]]:
        """
        Classify text blocks into header, footer, left column, right column.
        Header/footer boundaries are determined by vertical line extent if provided,
        otherwise fall back to percentage-based thresholds.
        """
        
        effective_header_y_max = header_y_max + 10 if header_y_max is not None else page_height * 0.15
        effective_footer_y_min = footer_y_min - 10 if footer_y_min is not None else page_height * 0.9
        
        regions = {
            'header': [],
            'footer': [],
            'left_column': [],
            'right_column': []
        }
        
        for block in text_blocks:
            x0, y0, x1, y1 = block.bbox
            
            if y1 < effective_header_y_max:
                regions['header'].append(block)
            elif y0 > effective_footer_y_min:
                regions['footer'].append(block)
            else:
                block_center_x = (x0 + x1) / 2
                if block_center_x < separator_x:
                    regions['left_column'].append(block)
                else:
                    regions['right_column'].append(block)
        
        return regions
    
    def blocks_to_text(self, blocks: List[TextBlock]) -> str:
        """
        Convert text blocks to continuous text, preserving reading order.
        """
        if not blocks:
            return ""
        
        sorted_blocks = sorted(blocks, key=lambda b: (b.bbox[1], b.bbox[0]))
        
        lines = []
        current_line_blocks = []
        current_line_y_max = -1
        
        for block in sorted_blocks:
            if not current_line_blocks or (block.bbox[1] < current_line_y_max + 10):
                current_line_blocks.append(block)
                current_line_y_max = max(current_line_y_max, block.bbox[3])
            else:
                if current_line_blocks:
                    lines.append(current_line_blocks)
                current_line_blocks = [block]
                current_line_y_max = block.bbox[3]
        
        if current_line_blocks:
            lines.append(current_line_blocks)
        
        text_lines = []
        for line_blocks in lines:
            line_text = " ".join(block.text for block in sorted(line_blocks, key=lambda b: b.bbox[0]))
            text_lines.append(line_text)
        
        return "\n".join(text_lines)
    
    def extract_page_layout(self, page_num: int) -> PageLayout:
        """Extract layout information from a single page"""
        page = self.doc[page_num]
        page_rect = page.rect
        
        # Get text blocks using LayoutLM
        text_blocks = self.get_text_blocks_from_layoutlm(page)
        
        # Find column separator
        separator_x, header_y_max, footer_y_min = self.find_column_separator(page, text_blocks)
        
        # Classify text regions
        regions = self.classify_text_regions(text_blocks, page_rect.height, separator_x, header_y_max, footer_y_min)
        
        # Convert regions to text
        header_text = self.blocks_to_text(regions['header'])
        footer_text = self.blocks_to_text(regions['footer'])
        left_column_text = self.blocks_to_text(regions['left_column'])
        right_column_text = self.blocks_to_text(regions['right_column'])
        
        # Gather metadata
        metadata = {
            'total_text_blocks_layoutlm': len(text_blocks), # From LayoutLM
            'header_blocks': len(regions['header']),
            'footer_blocks': len(regions['footer']),
            'left_column_blocks': len(regions['left_column']),
            'right_column_blocks': len(regions['right_column']),
            'vertical_lines_detected_count': len(self.detect_vertical_lines(page)), # Still from PyMuPDF
            'page_rect': [page_rect.x0, page_rect.y0, page_rect.x1, page_rect.y1],
            'header_y_boundary': header_y_max,
            'footer_y_boundary': footer_y_min
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
    
    def extract_all_pages(self) -> List[PageLayout]:
        """Extract layout information from all pages"""
        layouts = []
        for page_num in range(len(self.doc)):
            print(f"Processing page {page_num + 1}/{len(self.doc)} with LayoutLM...")
            layout = self.extract_page_layout(page_num)
            layouts.append(layout)
        return layouts
    
    def save_to_json(self, output_path: str, layouts: List[PageLayout]):
        """Save extracted layouts to JSON file"""
        data = {
            'pdf_path': self.pdf_path,
            'total_pages': len(self.doc),
            'pages': [asdict(layout) for layout in layouts]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def close(self):
        """Close the PDF document"""
        self.doc.close()

def main():
    pdf_path = "./data_dir/document.pdf"
    output_path = "./data_dir/extracted_layout_document_layoutlm.json"
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    extractor = None
    try:
        extractor = PDFColumnExtractor(pdf_path)
        
        layouts = extractor.extract_all_pages()
        
        extractor.save_to_json(output_path, layouts)
        
        print(f"\nProcessed {len(layouts)} pages with LayoutLM.")
        for i, layout in enumerate(layouts):
            print(f"\nPage {layout.page_number}:")
            print(f"  Header: {len(layout.header)} chars")
            print(f"  Footer: {len(layout.footer)} chars") 
            print(f"  Left Column: {len(layout.left_column)} chars")
            print(f"  Right Column: {len(layout.right_column)} chars")
            print(f"  Column separator at: {layout.column_separator_position:.1f}")
            print(f"  Header boundary Y: {layout.metadata.get('header_y_boundary', 'N/A'):.1f}")
            print(f"  Footer boundary Y: {layout.metadata.get('footer_y_boundary', 'N/A'):.1f}")

        if layouts:
            print(f"\nFirst page left column preview:")
            print(layouts[0].left_column[:200] + "..." if len(layouts[0].left_column) > 200 else layouts[0].left_column)
        
        print(f"\nResults saved to {output_path}")
        
    except FileNotFoundError:
        print(f"Error: PDF file not found at {pdf_path}. Please check the path.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc() # Print full traceback for debugging
    finally:
        if extractor is not None and extractor.doc is not None and not extractor.doc.is_closed:
            extractor.close()

if __name__ == "__main__":
    main()