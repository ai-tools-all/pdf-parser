# in pdf_parser.py
import fitz  # PyMuPDF
from typing import List, Dict, Tuple
from qna_orchestrator.qna_heuristics.data_models import Document, Page, TextBlock

class PDFParser:
    def __init__(self, config: Dict):
        self.full_config = config
        self.config = config.get("PARSER", {})

    def parse(self, pdf_path: str) -> Document:
        doc = fitz.open(pdf_path)
        document_obj = Document(pdf_path=pdf_path)

        for page_num, page in enumerate(doc):
            page_obj = Page(
                page_number=page_num + 1,
                page_width=page.rect.width,
                page_height=page.rect.height,
            )

            blocks = self._get_text_blocks(page)
            separator_x = self._find_column_separator(page, blocks)
            self._classify_blocks(page_obj, blocks, separator_x)

            # Generate raw text for inspection
            page_obj.raw_left_text = "\n".join(b.text for b in page_obj.left_column_blocks)
            page_obj.raw_right_text = "\n".join(b.text for b in page_obj.right_column_blocks)

            document_obj.pages.append(page_obj)

        doc.close()
        return document_obj

    def _get_text_blocks(self, page: fitz.Page) -> List[TextBlock]:
        raw_blocks = page.get_text("dict")["blocks"]
        text_blocks = []
        block_idx = 0
        
        # Load noise patterns from config
        noise_patterns = self.full_config.get("NOISE_PATTERNS", [])
        
        for b in raw_blocks:
            if "lines" not in b:
                continue
            for line in b["lines"]:
                if line["spans"]:
                    line_text = ""
                    font_size = 0
                    font_name = ""
                    for span in line["spans"]:
                        line_text += span["text"]
                        font_size = max(font_size, span.get("size", 0))
                        if not font_name:
                            font_name = span.get("font", "Unknown")

                    text = line_text.strip()
                    if not text:
                        continue
                    
                    # --- NOISE FILTERING ---
                    # Check if text contains any noise pattern (case insensitive)
                    is_noise = False
                    for pattern in noise_patterns:
                        if pattern.lower() in text.lower():
                            is_noise = True
                            break
                    
                    if is_noise:
                        continue
                    # ----------------------------
                    
                    text_blocks.append(TextBlock(
                        id=f"p{page.number + 1}-b{block_idx}",
                        page_number=page.number + 1,
                        text=text,
                        bbox=line["bbox"],
                        font_size=font_size,
                        font_name=font_name
                    ))
                    block_idx += 1
        # Sort blocks by reading order (top-to-bottom, left-to-right)
        return sorted(text_blocks, key=lambda b: (b.bbox[1], b.bbox[0]))

    def _find_column_separator(self, page: fitz.Page, blocks: List[TextBlock]) -> float:
        """
        Find dynamic column separator by analyzing actual text distribution
        """
        if not blocks:
            return page.rect.width / 2
        
        # Get x-coordinates of all text blocks
        x_coords = []
        for block in blocks:
            left_x = block.bbox[0]
            right_x = block.bbox[2]
            center_x = (left_x + right_x) / 2
            x_coords.extend([left_x, center_x, right_x])
        
        x_coords.sort()
        page_width = page.rect.width
        
        # Find the largest gap in the middle 60% of the page
        # This avoids edge cases and focuses on likely column separators
        start_range = page_width * 0.2
        end_range = page_width * 0.8
        
        largest_gap = 0
        best_separator = page_width / 2  # fallback
        
        for i in range(len(x_coords) - 1):
            gap_start = x_coords[i]
            gap_end = x_coords[i + 1]
            gap_size = gap_end - gap_start
            gap_center = (gap_start + gap_end) / 2
            
            # Only consider gaps in the middle region and larger than minimum threshold
            min_gap_size = page_width * 0.05  # 5% of page width minimum
            if (start_range <= gap_center <= end_range and 
                gap_size > largest_gap and 
                gap_size > min_gap_size):
                largest_gap = gap_size
                best_separator = gap_center
        
        return best_separator

    def _classify_blocks(self, page_obj: Page, blocks: List[TextBlock], separator_x: float):
        header_y = page_obj.page_height * self.config["HEADER_REGION_PERCENT"]
        footer_y = page_obj.page_height * self.config["FOOTER_REGION_PERCENT"]

        for block in blocks:
            center_y = (block.bbox[1] + block.bbox[3]) / 2
            center_x = (block.bbox[0] + block.bbox[2]) / 2

            if center_y < header_y or center_y > footer_y:
                page_obj.other_blocks.append(block)
            elif center_x < separator_x:
                page_obj.left_column_blocks.append(block)
            else:
                page_obj.right_column_blocks.append(block)