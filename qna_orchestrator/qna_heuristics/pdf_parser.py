# in pdf_parser.py
import fitz  # PyMuPDF
from typing import List, Dict, Tuple
from data_models import Document, Page, TextBlock

class PDFParser:
    def __init__(self, config: Dict):
        self.config = config["PARSER"]

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
        for b in raw_blocks:
            if "lines" not in b:
                continue
            for line in b["lines"]:
                if line["spans"]:
                    text = "".join(span["text"] for span in line["spans"]).strip()
                    if text:
                        text_blocks.append(TextBlock(
                            id=f"p{page.number + 1}-b{block_idx}",
                            page_number=page.number + 1,
                            text=text,
                            bbox=line["bbox"]
                        ))
                        block_idx += 1
        # Sort blocks by reading order (top-to-bottom, left-to-right)
        return sorted(text_blocks, key=lambda b: (b.bbox[1], b.bbox[0]))

    def _find_column_separator(self, page: fitz.Page, blocks: List[TextBlock]) -> float:
        # Simplified heuristic: assume separator is near the middle
        # A more robust implementation would analyze gaps in the x-distribution of text
        return page.rect.width / 2

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