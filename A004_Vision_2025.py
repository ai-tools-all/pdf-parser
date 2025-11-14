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
    page_number: int

@dataclass
class Question:
    question_number: int
    question_text: str
    page_number: int
    column: str  # 'left' or 'right'
    bbox: Optional[Tuple[float, float, float, float]] = None
    metadata: Optional[Dict] = None

class VisionIASParser:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.questions = []

    def detect_vertical_lines(self, page) -> List[Tuple[float, float, float, float]]:
        """Detect vertical lines in the page that might separate columns"""
        vertical_lines = []

        try:
            drawings = page.get_drawings()
            for drawing in drawings:
                if "items" in drawing:
                    for item in drawing["items"]:
                        if len(item) >= 5 and item[0] == "l":  # line
                            x1, y1, x2, y2 = item[1:5]
                            # Check if it's a vertical line
                            if abs(x2 - x1) < 5 and abs(y2 - y1) > 100:
                                vertical_lines.append((x1, y1, x2, y2))
        except Exception as e:
            print(f"Warning: Could not detect vertical lines on page {page.number}: {e}")

        return vertical_lines

    def get_text_blocks(self, page, page_num: int) -> List[TextBlock]:
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
                                    bbox=tuple(bbox[:4]),
                                    font_size=font_size,
                                    font_name=font_name,
                                    page_number=page_num
                                ))
        except Exception as e:
            print(f"Warning: Error extracting text blocks from page {page.number}: {e}")

        return text_blocks

    def find_column_separator(self, page, text_blocks: List[TextBlock]) -> float:
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

        # If no vertical lines found, use page center
        return page_width / 2

    def is_header_or_footer(self, block: TextBlock, page_height: float) -> bool:
        """Check if a text block is likely a header or footer"""
        y_center = (block.bbox[1] + block.bbox[3]) / 2

        # Top 10% or bottom 5% of page
        if y_center < page_height * 0.10 or y_center > page_height * 0.95:
            # Additional checks for common footer/header patterns
            text_lower = block.text.lower()
            footer_indicators = ['page', 'copyright', '©', 'www.', '.com', '.org',
                               'all rights reserved', 'vision ias']
            if any(indicator in text_lower for indicator in footer_indicators):
                return True
            # Short text with numbers (likely page numbers)
            if len(block.text.strip()) < 50 and any(char.isdigit() for char in block.text):
                return True

        return False

    def classify_blocks_into_columns(self, text_blocks: List[TextBlock],
                                     separator_x: float, page_height: float) -> Dict[str, List[TextBlock]]:
        """Classify text blocks into left and right columns, excluding headers/footers"""
        columns = {
            'left': [],
            'right': []
        }

        for block in text_blocks:
            # Skip headers and footers
            if self.is_header_or_footer(block, page_height):
                continue

            center_x = (block.bbox[0] + block.bbox[2]) / 2

            if center_x < separator_x:
                columns['left'].append(block)
            else:
                columns['right'].append(block)

        return columns

    def extract_questions_from_blocks(self, blocks: List[TextBlock], column: str) -> List[Question]:
        """Extract questions from text blocks in a column"""
        if not blocks:
            return []

        # Sort blocks by position (top to bottom)
        sorted_blocks = sorted(blocks, key=lambda b: (b.bbox[1], b.bbox[0]))

        # Combine blocks into continuous text with position tracking
        combined_text = ""
        block_positions = []

        for block in sorted_blocks:
            start_pos = len(combined_text)
            combined_text += block.text + " "
            end_pos = len(combined_text)
            block_positions.append((start_pos, end_pos, block))

        # Detect question patterns
        # Common patterns: "1.", "1)", "Q1.", "Q.1", "Question 1"
        question_pattern = r'(?:^|\n)\s*(?:Q\.?\s*)?(\d+)[\.\)]\s+'

        questions = []
        matches = list(re.finditer(question_pattern, combined_text, re.MULTILINE))

        for i, match in enumerate(matches):
            question_num = int(match.group(1))
            question_start = match.start()

            # Find question end (next question start or end of text)
            if i < len(matches) - 1:
                question_end = matches[i + 1].start()
            else:
                question_end = len(combined_text)

            question_text = combined_text[question_start:question_end].strip()

            # Find the block containing this question for position info
            question_bbox = None
            question_page = None
            for start_pos, end_pos, block in block_positions:
                if start_pos <= question_start < end_pos:
                    question_bbox = block.bbox
                    question_page = block.page_number
                    break

            questions.append(Question(
                question_number=question_num,
                question_text=question_text,
                page_number=question_page if question_page else (blocks[0].page_number if blocks else 0),
                column=column,
                bbox=question_bbox,
                metadata={'raw_match': match.group(0)}
            ))

        return questions

    def merge_questions_in_reading_order(self, left_questions: List[Question],
                                        right_questions: List[Question]) -> List[Question]:
        """Merge questions from left and right columns in reading order"""
        # For two-column layout, reading order is:
        # Left column (top to bottom) -> Right column (top to bottom)

        all_questions = []

        # Add left column questions first
        all_questions.extend(sorted(left_questions, key=lambda q: q.question_number))

        # Add right column questions
        all_questions.extend(sorted(right_questions, key=lambda q: q.question_number))

        # Sort by question number to ensure proper order
        all_questions = sorted(all_questions, key=lambda q: q.question_number)

        return all_questions

    def extract_all_questions(self) -> List[Question]:
        """Extract all questions from the PDF in reading order"""
        all_questions = []

        for page_num in range(len(self.doc)):
            try:
                page = self.doc[page_num]
                page_rect = page.rect

                # Get text blocks
                text_blocks = self.get_text_blocks(page, page_num + 1)

                if not text_blocks:
                    print(f"Page {page_num + 1}: No text blocks found")
                    continue

                # Find column separator
                separator_x = self.find_column_separator(page, text_blocks)

                # Classify blocks into columns
                columns = self.classify_blocks_into_columns(text_blocks, separator_x, page_rect.height)

                print(f"Page {page_num + 1}: Left column blocks: {len(columns['left'])}, Right column blocks: {len(columns['right'])}")

                # Extract questions from each column
                left_questions = self.extract_questions_from_blocks(columns['left'], 'left')
                right_questions = self.extract_questions_from_blocks(columns['right'], 'right')

                print(f"Page {page_num + 1}: Found {len(left_questions)} questions in left column, {len(right_questions)} in right column")

                # Merge questions in reading order
                page_questions = self.merge_questions_in_reading_order(left_questions, right_questions)
                all_questions.extend(page_questions)

            except Exception as e:
                print(f"Error processing page {page_num + 1}: {e}")
                import traceback
                traceback.print_exc()

        return all_questions

    def save_to_json(self, output_path: str, questions: List[Question]):
        """Save extracted questions to JSON file"""
        data = {
            'pdf_path': self.pdf_path,
            'total_questions': len(questions),
            'questions': [asdict(q) for q in questions]
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def save_to_markdown(self, output_path: str, questions: List[Question]):
        """Save extracted questions to Markdown file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# Vision IAS Questions\n\n")
            f.write(f"**Source:** {self.pdf_path}\n\n")
            f.write(f"**Total Questions:** {len(questions)}\n\n")
            f.write("---\n\n")

            for question in questions:
                f.write(f"## Question {question.question_number}\n\n")
                f.write(f"{question.question_text}\n\n")
                f.write(f"*Page: {question.page_number}, Column: {question.column}*\n\n")
                f.write("---\n\n")

    def close(self):
        """Close the PDF document"""
        self.doc.close()


def main():
    """Main function to parse Vision IAS PDF"""
    # Configuration
    pdf_path = "./data_dir/vision_ias.pdf"  # Replace with your PDF path
    json_output = "./data_dir/004_vision_questions.json"
    md_output = "./data_dir/004_vision_questions.md"

    # Check if PDF file exists
    import os
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file '{pdf_path}' not found.")
        print("Please update the pdf_path variable with the correct path to your Vision IAS PDF file.")
        return

    try:
        print(f"Processing Vision IAS PDF: {pdf_path}")
        parser = VisionIASParser(pdf_path)

        # Extract all questions
        print("\nExtracting questions from two-column layout...")
        questions = parser.extract_all_questions()

        # Save results
        parser.save_to_json(json_output, questions)
        parser.save_to_markdown(md_output, questions)

        # Print summary
        print(f"\n{'='*60}")
        print(f"EXTRACTION SUMMARY")
        print(f"{'='*60}")
        print(f"Total questions extracted: {len(questions)}")

        if questions:
            print(f"\nFirst question: Q{questions[0].question_number}")
            print(f"Last question: Q{questions[-1].question_number}")

            # Count questions by page
            page_counts = {}
            for q in questions:
                page_counts[q.page_number] = page_counts.get(q.page_number, 0) + 1

            print(f"\nQuestions per page:")
            for page, count in sorted(page_counts.items()):
                print(f"  Page {page}: {count} questions")

            # Show first few questions as preview
            print(f"\n{'='*60}")
            print(f"PREVIEW (First 3 questions)")
            print(f"{'='*60}")
            for question in questions[:3]:
                print(f"\nQ{question.question_number} (Page {question.page_number}, {question.column} column):")
                # Show first 200 chars of question text
                preview = question.question_text[:200]
                if len(question.question_text) > 200:
                    preview += "..."
                print(f"{preview}")

        parser.close()

        print(f"\n{'='*60}")
        print(f"Results saved to:")
        print(f"  JSON: {json_output}")
        print(f"  Markdown: {md_output}")
        print(f"{'='*60}")

    except FileNotFoundError:
        print(f"Error: Could not find PDF file '{pdf_path}'")
    except Exception as e:
        print(f"Error processing PDF: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
