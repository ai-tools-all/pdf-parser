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
    page_number: int

@dataclass
class Question:
    """Data structure for extracted questions."""
    question_number: int
    question_text: str
    page_number: int
    column: str  # 'left' or 'right'
    bbox: Optional[Tuple[float, float, float, float]] = None
    metadata: Optional[Dict] = None

class VisionIASExtractor:
    """
    PDF layout extractor specialized for Vision IAS two-column format.

    Implements the PDFLayoutExtractor protocol for compatibility with
    the testing framework. Specializes in extracting questions from
    two-column layouts following the reading order:
    left column (top→bottom) → right column (top→bottom).

    Args:
        pdf_path: Path to the PDF file to process
    """

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)

    def detect_vertical_lines(self, page) -> List[Tuple[float, float, float, float]]:
        """Detect vertical lines in the page that might separate columns."""
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
        """Extract text blocks with their positions and formatting."""
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
            # Fallback to simple text extraction
            try:
                text = page.get_text()
                if text.strip():
                    page_rect = page.rect
                    text_blocks.append(TextBlock(
                        text=text.strip(),
                        bbox=(page_rect.x0, page_rect.y0, page_rect.x1, page_rect.y1),
                        font_size=12.0,  # Default font size
                        font_name="Unknown",
                        page_number=page_num
                    ))
            except:
                pass

        return text_blocks

    def find_column_separator(self, page, text_blocks: List[TextBlock]) -> float:
        """Find the column separator position."""
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

        # Try different separator positions and find the best one
        for separator_x in range(int(page_width * 0.3), int(page_width * 0.7), 10):
            left_count = sum(1 for block in text_blocks if block.bbox[2] < separator_x)
            right_count = sum(1 for block in text_blocks if block.bbox[0] > separator_x)

            if left_count > 0 and right_count > 0:
                return float(separator_x)

        return page_width / 2

    def is_header_or_footer(self, block: TextBlock, page_height: float) -> bool:
        """Check if a text block is likely a header or footer."""
        y_center = (block.bbox[1] + block.bbox[3]) / 2

        # Top 10% or bottom 5% of page
        if y_center < page_height * 0.10:
            return True

        if y_center > page_height * 0.95:
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

    def classify_text_regions(self, text_blocks: List[TextBlock],
                             separator_x: float, page_height: float) -> Dict[str, List[TextBlock]]:
        """Classify text blocks into header, footer, left column, right column."""
        regions = {
            'header': [],
            'footer': [],
            'left_column': [],
            'right_column': []
        }

        for block in text_blocks:
            center_x = (block.bbox[0] + block.bbox[2]) / 2
            y_center = (block.bbox[1] + block.bbox[3]) / 2

            # Classify as header or footer
            if y_center < page_height * 0.10:
                regions['header'].append(block)
            elif self.is_header_or_footer(block, page_height):
                regions['footer'].append(block)
            else:
                # Classify by horizontal position for main content
                if center_x < separator_x:
                    regions['left_column'].append(block)
                else:
                    regions['right_column'].append(block)

        return regions

    def blocks_to_text(self, blocks: List[TextBlock]) -> str:
        """Convert text blocks to continuous text."""
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
        """
        Extract layout information from a single page.

        Args:
            page_num: 0-indexed page number

        Returns:
            PageLayout object with extracted information
        """
        try:
            page = self.doc[page_num]
            page_rect = page.rect

            # Get text blocks
            text_blocks = self.get_text_blocks(page, page_num + 1)

            # Find column separator
            separator_x = self.find_column_separator(page, text_blocks)

            # Classify text regions
            regions = self.classify_text_regions(text_blocks, separator_x, page_rect.height)

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
        """
        Extract layout information from all pages in the PDF.

        Returns:
            List of PageLayout objects, one per page
        """
        layouts = []
        for page_num in range(len(self.doc)):
            layout = self.extract_page_layout(page_num)
            layouts.append(layout)
        return layouts

    def close(self) -> None:
        """Clean up resources (close PDF file handles)."""
        self.doc.close()

    # Additional Vision IAS specific methods for question extraction

    def extract_questions_from_text(self, text: str, column: str, page_num: int) -> List[Question]:
        """
        Extract questions from text in a column.

        Args:
            text: The text to extract questions from
            column: Column identifier ('left' or 'right')
            page_num: Page number for the questions

        Returns:
            List of Question objects
        """
        if not text:
            return []

        # Detect question patterns
        # Common patterns: "1.", "1)", "Q1.", "Q.1", "Question 1"
        question_pattern = r'(?:^|\n)\s*(?:Q\.?\s*)?(\d+)[\.\)]\s+'

        questions = []
        matches = list(re.finditer(question_pattern, text, re.MULTILINE))

        for i, match in enumerate(matches):
            question_num = int(match.group(1))
            question_start = match.start()

            # Find question end (next question start or end of text)
            if i < len(matches) - 1:
                question_end = matches[i + 1].start()
            else:
                question_end = len(text)

            question_text = text[question_start:question_end].strip()

            questions.append(Question(
                question_number=question_num,
                question_text=question_text,
                page_number=page_num,
                column=column,
                bbox=None,
                metadata={'raw_match': match.group(0)}
            ))

        return questions

    def extract_all_questions(self) -> List[Question]:
        """
        Extract all questions from the PDF in reading order.

        This is a Vision IAS specific method that extracts questions
        following the two-column reading order.

        Returns:
            List of Question objects sorted by question number
        """
        all_questions = []

        for page_num in range(len(self.doc)):
            try:
                # Use the protocol method to get page layout
                layout = self.extract_page_layout(page_num)

                # Extract questions from each column
                left_questions = self.extract_questions_from_text(
                    layout.left_column, 'left', layout.page_number
                )
                right_questions = self.extract_questions_from_text(
                    layout.right_column, 'right', layout.page_number
                )

                # Combine questions
                page_questions = left_questions + right_questions
                all_questions.extend(page_questions)

                print(f"Page {layout.page_number}: Found {len(left_questions)} questions in left column, "
                      f"{len(right_questions)} in right column")

            except Exception as e:
                print(f"Error extracting questions from page {page_num + 1}: {e}")

        # Sort by question number
        all_questions = sorted(all_questions, key=lambda q: q.question_number)

        return all_questions

    def save_to_json(self, output_path: str, layouts: List[PageLayout]):
        """Save extracted layouts to JSON file."""
        data = {
            'pdf_path': self.pdf_path,
            'total_pages': len(layouts),
            'pages': [asdict(layout) for layout in layouts]
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def save_questions_to_json(self, output_path: str, questions: List[Question]):
        """Save extracted questions to JSON file."""
        data = {
            'pdf_path': self.pdf_path,
            'total_questions': len(questions),
            'questions': [asdict(q) for q in questions]
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def save_questions_to_markdown(self, output_path: str, questions: List[Question]):
        """Save extracted questions to Markdown file."""
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


def main():
    """Main function to parse Vision IAS PDF."""
    # Configuration
    pdf_path = "./data_dir/vision_ias.pdf"  # Replace with your PDF path
    layout_json = "./data_dir/004_vision_layout.json"
    questions_json = "./data_dir/004_vision_questions.json"
    questions_md = "./data_dir/004_vision_questions.md"

    # Check if PDF file exists
    import os
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file '{pdf_path}' not found.")
        print("Please update the pdf_path variable with the correct path to your Vision IAS PDF file.")
        return

    try:
        print(f"Processing Vision IAS PDF: {pdf_path}")
        extractor = VisionIASExtractor(pdf_path)

        # Extract page layouts (protocol method)
        print("\nExtracting page layouts...")
        layouts = extractor.extract_all_pages()
        extractor.save_to_json(layout_json, layouts)
        print(f"Page layouts saved to: {layout_json}")

        # Extract questions (Vision IAS specific)
        print("\nExtracting questions from two-column layout...")
        questions = extractor.extract_all_questions()

        # Save question results
        extractor.save_questions_to_json(questions_json, questions)
        extractor.save_questions_to_markdown(questions_md, questions)

        # Print summary
        print(f"\n{'='*60}")
        print(f"EXTRACTION SUMMARY")
        print(f"{'='*60}")
        print(f"Total pages processed: {len(layouts)}")
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

        extractor.close()

        print(f"\n{'='*60}")
        print(f"Results saved to:")
        print(f"  Page layouts (JSON): {layout_json}")
        print(f"  Questions (JSON): {questions_json}")
        print(f"  Questions (Markdown): {questions_md}")
        print(f"{'='*60}")

    except FileNotFoundError:
        print(f"Error: Could not find PDF file '{pdf_path}'")
    except Exception as e:
        print(f"Error processing PDF: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
