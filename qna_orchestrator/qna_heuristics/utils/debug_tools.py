"""
Debug Utilities for PDF Parser Analysis
Run these functions to inspect parser behavior granularly.
"""
import json
import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Dict, Optional

class Debugger:
    def __init__(self, json_path: str = "output/01_analyzed_document.json",
                 mcq_path: str = "output/02_final_mcqs.json"):
        self.json_path = Path(json_path)
        self.mcq_path = Path(mcq_path)
        
        # Load analysis data
        if not self.json_path.exists():
            print(f"⚠️ File not found: {self.json_path}")
            self.data = None
        else:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        
        # Load MCQ data
        if not self.mcq_path.exists():
            print(f"⚠️ MCQ file not found: {self.mcq_path}")
            self.mcq_data = None
        else:
            with open(self.mcq_path, 'r', encoding='utf-8') as f:
                self.mcq_data = json.load(f)

    def inspect_mcq_stats(self):
        """Quick summary of extracted MCQs with gap detection."""
        if not self.mcq_data:
            print("❌ No MCQ data found.")
            return
        
        count = len(self.mcq_data)
        print(f"\n--- 📊 MCQ Extraction Stats ---")
        print(f"Total MCQs Found: {count}")
        
        if count > 0:
            print("\nFirst 3 Questions:")
            for mcq in self.mcq_data[:3]:
                q_text = mcq.get('question_text', '')[:60].replace('\n', ' ')
                print(f"  Q{mcq.get('question_number')}: {q_text}...")
            
            print("\nLast 3 Questions:")
            for mcq in self.mcq_data[-3:]:
                q_text = mcq.get('question_text', '')[:60].replace('\n', ' ')
                print(f"  Q{mcq.get('question_number')}: {q_text}...")

            # Check for gaps
            nums = sorted([m['question_number'] for m in self.mcq_data])
            expected = list(range(nums[0], nums[-1] + 1))
            missing = set(expected) - set(nums)
            if missing:
                print(f"\n⚠️ Missing Question Numbers: {sorted(list(missing))}")
            else:
                print("\n✅ No gaps in question sequence.")

    def inspect_page_blocks(self, page_num: int):
        """
        Visualizes the reading order of a specific page (1-indexed).
        Useful to see if 'left-column first' logic works.
        """
        if not self.data: return
        
        # Find page (0-indexed in list, but page_number is 1-indexed)
        page = next((p for p in self.data['pages'] if p['page_number'] == page_num), None)
        if not page:
            print(f"Page {page_num} not found.")
            return

        print(f"\n--- 🔍 Inspection: Page {page_num} ---")
        
        # Combine all blocks as the Orchestrator sees them
        all_blocks = []
        all_blocks.extend(page.get('left_column_blocks', []))
        all_blocks.extend(page.get('right_column_blocks', []))
        all_blocks.extend(page.get('other_blocks', []))
        
        # Sort usually happens in Assembler, let's simulate that
        # (Assuming standard left->right sort strategy)
        left = sorted(page.get('left_column_blocks', []), key=lambda b: b['bbox'][1])
        right = sorted(page.get('right_column_blocks', []), key=lambda b: b['bbox'][1])
        other = sorted(page.get('other_blocks', []), key=lambda b: b['bbox'][1])
        
        sorted_blocks = left + right + other # Simplified reading order

        for i, block in enumerate(sorted_blocks):
            text = block['text'][:60].replace('\n', ' ')
            # Show heuristics results if any
            is_q = "❌"
            q_num = ""
            for h in block.get('analysis_results', []):
                if h.get('heuristic_name') == 'question_start' and h.get('is_question_start'):
                    is_q = "✅"
                    q_num = f"Q{h.get('question_number')}"
            
            print(f"[{i:03d}] {is_q} {q_num:<4} | {text:<60} | ID: {block['id']}")

    def find_question_boundary(self, q_num: int):
        """
        Locates exactly which text block triggered Question X start.
        """
        if not self.data: return
        print(f"\n--- 🎯 Finding Start of Q{q_num} ---")
        
        found = False
        for page in self.data['pages']:
            all_blocks = page['left_column_blocks'] + page['right_column_blocks']
            for block in all_blocks:
                for res in block.get('analysis_results', []):
                    if (res.get('heuristic_name') == 'question_start' and 
                        res.get('question_number') == str(q_num)): # regex usually returns str
                        
                        print(f"Found on Page {page['page_number']}:")
                        print(f"Text: {block['text']}")
                        print(f"Block ID: {block['id']}")
                        print(f"Heuristic Confidence: {res.get('confidence')}")
                        found = True
        
        if not found:
            print(f"Question {q_num} start signal not found in analysis data.")

    def visualize_on_pdf(self, pdf_path: str, output_path: str = "debug_visual.pdf"):
        """
        Draws bounding boxes on the actual PDF to verify layout detection.
        Green = Left Col, Blue = Right Col, Red = Other (Header/Footer)
        """
        if not self.data: return
        
        try:
            doc = fitz.open(pdf_path)
            print(f"\n--- 🎨 Drawing Layout Visualization ---")
            
            for page_data in self.data['pages']:
                p_num = page_data['page_number'] - 1
                if p_num >= len(doc): continue
                
                page = doc[p_num]
                
                # Helper to draw
                def draw(blocks, color):
                    for b in blocks:
                        rect = fitz.Rect(b['bbox'])
                        page.draw_rect(rect, color=color, width=0.5)

                draw(page_data.get('left_column_blocks', []), color=(0, 1, 0)) # Green
                draw(page_data.get('right_column_blocks', []), color=(0, 0, 1)) # Blue
                draw(page_data.get('other_blocks', []), color=(1, 0, 0))       # Red

            doc.save(output_path)
            print(f"Saved visualization to: {output_path}")
        except Exception as e:
            print(f"Error drawing PDF: {e}")

# --- Quick CLI ---
if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Parser Debugger")
    parser.add_argument('--action', choices=['page', 'question', 'visualize', 'stats'], required=True)
    parser.add_argument('--target', help="Page number or Question number")
    parser.add_argument('--pdf', help="Path to original PDF (for visualization)")
    parser.add_argument('--json', default="output/01_analyzed_document.json", help="Path to analysis JSON")
    parser.add_argument('--mcq', default="output/02_final_mcqs.json", help="Path to MCQ JSON")
    
    args = parser.parse_args()
    
    dbg = Debugger(args.json, args.mcq)
    
    if args.action == 'stats':
        dbg.inspect_mcq_stats()
    elif args.action == 'page':
        if not args.target:
            print("Error: --target PAGE_NUM required")
        else:
            dbg.inspect_page_blocks(int(args.target))
    elif args.action == 'question':
        if not args.target:
            print("Error: --target QUESTION_NUM required")
        else:
            dbg.find_question_boundary(int(args.target))
    elif args.action == 'visualize':
        if not args.pdf:
            print("Error: --pdf path required for visualization")
        else:
            dbg.visualize_on_pdf(args.pdf)
