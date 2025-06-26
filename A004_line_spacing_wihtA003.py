import fitz  # PyMuPDF
import json
import re
import statistics
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict

# --- Data Classes (from your provided code) ---

@dataclass(frozen=True)  # Add frozen=True to make it hashable
class TextBlock:
    text: str
    bbox: Tuple[float, float, float, float]  # x0, y0, x1, y1
    font_size: float
    font_name: str
    page_num: int

@dataclass(frozen=True)  # Add frozen=True here
class PageLayout:
    page_number: int
    header: List[TextBlock]
    footer: List[TextBlock]
    left_column: List[TextBlock]
    right_column: List[TextBlock]
    page_width: float
    page_height: float
    column_separator_position: Optional[float]
    metadata: Dict

# --- PDF Parser (Modified from your provided code) ---

class PDFColumnExtractor:
    """
    Parses a PDF to extract text blocks and classify them into layout regions.
    Modified to return lists of TextBlock objects instead of just strings.
    """
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)

    def get_text_blocks(self, page) -> List[TextBlock]:
        """Extract text blocks with their positions and formatting."""
        text_blocks = []
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                line_text = ""
                font_size = 0
                font_name = ""
                for span in line["spans"]:
                    line_text += span["text"]
                    font_size = max(font_size, span.get("size", 0))
                    if not font_name:
                        font_name = span.get("font", "")
                if line_text.strip():
                    text_blocks.append(TextBlock(
                        text=line_text.strip(),
                        bbox=line["bbox"],
                        font_size=font_size,
                        font_name=font_name,
                        page_num=page.number
                    ))
        return sorted(text_blocks, key=lambda b: (b.bbox[1], b.bbox[0]))
    
    def find_column_separator(self, page, text_blocks: List[TextBlock]) -> Optional[float]:
        page_width = page.rect.width
        # A simple heuristic: check for a gap in the middle 40% of the page
        x_coords = [b.bbox[0] for b in text_blocks] + [b.bbox[2] for b in text_blocks]
        if not x_coords:
            return page_width / 2

        min_x, max_x = min(x_coords), max(x_coords)
        scan_start = min_x + (max_x - min_x) * 0.3
        scan_end = min_x + (max_x - min_x) * 0.7

        best_gap = 0
        best_separator = page_width / 2

        for x in range(int(scan_start), int(scan_end), 5):
            blocks_to_left = [b for b in text_blocks if b.bbox[2] < x]
            blocks_to_right = [b for b in text_blocks if b.bbox[0] > x]
            
            if not blocks_to_left or not blocks_to_right:
                continue

            closest_right_edge = max(b.bbox[2] for b in blocks_to_left)
            closest_left_edge = min(b.bbox[0] for b in blocks_to_right)

            gap = closest_left_edge - closest_right_edge
            if gap > best_gap:
                best_gap = gap
                best_separator = x

        return best_separator if best_gap > 10 else page_width / 2 # Require at least 10 points gap

    def classify_text_regions(self, page, text_blocks: List[TextBlock], separator_x: float) -> Dict[str, List[TextBlock]]:
        page_height = page.rect.height
        header_threshold = page_height * 0.12
        footer_threshold = page_height * 0.90

        regions = {'header': [], 'footer': [], 'left_column': [], 'right_column': []}
        
        for block in text_blocks:
            center_y = (block.bbox[1] + block.bbox[3]) / 2
            center_x = (block.bbox[0] + block.bbox[2]) / 2

            if center_y < header_threshold:
                regions['header'].append(block)
            elif center_y > footer_threshold:
                regions['footer'].append(block)
            else:
                if center_x < separator_x:
                    regions['left_column'].append(block)
                else:
                    regions['right_column'].append(block)
        return regions

    def extract_page_layout(self, page_num: int) -> PageLayout:
        page = self.doc[page_num]
        text_blocks = self.get_text_blocks(page)
        separator_x = self.find_column_separator(page, text_blocks)
        regions = self.classify_text_regions(page, text_blocks, separator_x)
        
        return PageLayout(
            page_number=page_num + 1,
            header=tuple(regions['header']),  # Convert to tuple
            footer=tuple(regions['footer']),  # Convert to tuple
            left_column=tuple(regions['left_column']),  # Convert to tuple
            right_column=tuple(regions['right_column']),  # Convert to tuple
            page_width=page.rect.width,
            page_height=page.rect.height,
            column_separator_position=separator_x,
            metadata={'total_blocks': len(text_blocks)}
        )

    def extract_all_pages(self) -> List[PageLayout]:
        return [self.extract_page_layout(i) for i in range(len(self.doc))]

    def close(self):
        self.doc.close()

# --- New MCQ Extractor with Layout Heuristics ---

class MCQExtractorWithLayout:
    def __init__(self, page_layouts: List[PageLayout]):
        self.layouts = page_layouts
        self.all_blocks = self._get_all_blocks_sorted()

    def _get_all_blocks_sorted(self) -> List[TextBlock]:
        """Gathers all text blocks from all regions and sorts them globally."""
        blocks = []
        for layout in self.layouts:
            blocks.extend(layout.header)
            blocks.extend(layout.left_column)
            blocks.extend(layout.right_column)
            blocks.extend(layout.footer)
        # Sort by page, then y-position, then x-position
        return sorted(blocks, key=lambda b: (b.page_num, b.bbox[1], b.bbox[0]))

    def _calculate_normal_spacing(self, blocks: List[TextBlock]) -> float:
        """Calculates the normal (median) line spacing for a list of blocks."""
        gaps = []
        if len(blocks) < 2:
            return 5.0  # Default spacing

        for i in range(1, len(blocks)):
            prev_block = blocks[i-1]
            curr_block = blocks[i]
            gap = curr_block.bbox[1] - prev_block.bbox[3]
            # Only consider positive, reasonable gaps for line spacing
            if 0 < gap < (prev_block.font_size * 2):
                gaps.append(gap)
        
        return statistics.median(gaps) if gaps else 5.0

    def _find_question_starts(self) -> List[TextBlock]:
        """
        Finds start of questions using the vertical spacing heuristic,
        focusing on the left column.
        """
        question_starts = []
        question_pattern = re.compile(r'^\d+\.\s+')

        for layout in self.layouts:
            left_col_blocks = layout.left_column
            if len(left_col_blocks) < 2:
                continue

            normal_spacing = self._calculate_normal_spacing(left_col_blocks)
            spacing_threshold = normal_spacing * 1.5  # Heuristic: gap must be 50% larger than normal

            for i in range(1, len(left_col_blocks)):
                prev_block = left_col_blocks[i-1]
                curr_block = left_col_blocks[i]

                if question_pattern.match(curr_block.text):
                    gap = curr_block.bbox[1] - prev_block.bbox[3]
                    if gap > spacing_threshold:
                        question_starts.append(curr_block)
        return question_starts

    def _find_answer_starts(self) -> List[TextBlock]:
        """Finds all blocks that start with 'Ans:'."""
        answer_starts = []
        for block in self.all_blocks:
            if block.text.strip().lower().startswith('ans:'):
                answer_starts.append(block)
        return answer_starts
    
    def _blocks_to_string(self, blocks: List[TextBlock]) -> str:
        """Converts a list of TextBlock objects into a formatted string."""
        return "\n".join(b.text for b in blocks)

    def parse_question_block(self, text: str) -> Optional[Dict]:
        """Parses question text and options from a string."""
        match = re.match(r'(\d+)\.\s*(.*)', text, re.DOTALL)
        if not match: return None
        
        question_number = int(match.group(1))
        content = match.group(2).strip()
        
        option_matches = list(re.finditer(r'^\s*\(([a-d])\)\s*(.*)', content, re.MULTILINE | re.IGNORECASE))
        
        if not option_matches:
            question_text = content
            options = {}
        else:
            first_option_start = option_matches[0].start()
            question_text = content[:first_option_start].strip()
            options = {m.group(1).lower(): m.group(2).strip() for m in option_matches}

        return {"question_number": question_number, "question_text": question_text, "options": options}

    def parse_answer_explanation(self, text: str) -> Optional[Dict]:
        """Parses the answer choice and explanation from a string."""
        match = re.match(r'Ans:\s*\(?([a-d])\)?\s*(.*)', text, re.IGNORECASE | re.DOTALL)
        if match:
            return {"answer_choice": match.group(1).lower(), "explanation": match.group(2).strip()}
        return None

    def extract(self) -> List[Dict]:
        """Main extraction method using layout-aware markers."""
        q_starts = self._find_question_starts()
        a_starts = self._find_answer_starts()

        # Create a unified list of markers
        markers = []
        for block in q_starts: markers.append({'type': 'q_start', 'block': block})
        for block in a_starts: markers.append({'type': 'a_start', 'block': block})
        
        # Sort markers globally by their position in the document
        markers.sort(key=lambda m: (m['block'].page_num, m['block'].bbox[1]))

        # Create a lookup from block object to its global index
        block_to_idx = {block: i for i, block in enumerate(self.all_blocks)}

        mcqs = []
        for i, marker in enumerate(markers):
            if marker['type'] == 'a_start':
                # Find the question this answer belongs to
                # It must be the most recent 'q_start' before this 'a_start'
                owning_question_marker_idx = -1
                for j in range(i - 1, -1, -1):
                    if markers[j]['type'] == 'q_start':
                        owning_question_marker_idx = j
                        break
                
                if owning_question_marker_idx == -1:
                    continue # Orphan answer, skip

                q_start_block = markers[owning_question_marker_idx]['block']
                a_start_block = marker['block']
                
                # Define the end of the explanation block
                # It ends right before the next question starts
                next_q_start_block = None
                for j in range(owning_question_marker_idx + 1, len(markers)):
                    if markers[j]['type'] == 'q_start':
                        next_q_start_block = markers[j]['block']
                        break
                
                # Get the slice of all_blocks for each part
                q_start_idx = block_to_idx[q_start_block]
                a_start_idx = block_to_idx[a_start_block]
                
                q_slice = self.all_blocks[q_start_idx : a_start_idx]
                
                if next_q_start_block:
                    a_end_idx = block_to_idx[next_q_start_block]
                    a_slice = self.all_blocks[a_start_idx : a_end_idx]
                else: # Last question in the document
                    a_slice = self.all_blocks[a_start_idx:]

                # Parse the blocks
                q_data = self.parse_question_block(self._blocks_to_string(q_slice))
                a_data = self.parse_answer_explanation(self._blocks_to_string(a_slice))

                if q_data and a_data:
                    # Check for duplicates before adding
                    if not any(q['question_number'] == q_data['question_number'] for q in mcqs):
                        mcqs.append({
                            "question_number": q_data["question_number"],
                            "question_text": q_data["question_text"],
                            "options": q_data["options"],
                            "answer": a_data["answer_choice"],
                            "explanation": a_data["explanation"]
                        })
        
        return sorted(mcqs, key=lambda x: x['question_number'])


def main():
    pdf_path = "./data_dir/document.pdf"
    output_json_path = "./data_dir/004_extracted_mcqs_with_layout.json"
    
    # --- Step 1: Extract detailed layout from PDF ---
    print(f"Processing PDF: {pdf_path}")
    layout_extractor = PDFColumnExtractor(pdf_path)
    page_layouts = layout_extractor.extract_all_pages()
    layout_extractor.close()
    print(f"Extracted layout data for {len(page_layouts)} pages.")

    # --- Step 2: Use layout data to extract MCQs ---
    print("Applying layout-aware heuristics to extract MCQs...")
    mcq_extractor = MCQExtractorWithLayout(page_layouts)
    extracted_data = mcq_extractor.extract()
    print(f"Successfully extracted {len(extracted_data)} MCQs.")

    # --- Step 3: Save results to a JSON file ---
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(extracted_data, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {output_json_path}")

    # Optional: Print the first extracted question for verification
    if extracted_data:
        print("\n--- First Extracted MCQ ---")
        print(json.dumps(extracted_data[0], indent=2))


if __name__ == "__main__":
    main()