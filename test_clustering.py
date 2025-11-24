import json
import sys
import os
from types import SimpleNamespace

# Ensure path is set to import orchestrator modules
sys.path.append(os.getcwd())

from qna_orchestrator.qna_heuristics.heuristics.clustering import detect_cluster_break
from qna_orchestrator.qna_heuristics.data_models import TextBlock, AnalysisContext

def test_heuristic_on_json(json_path):
    print(f"--- Testing HDBSCAN Clustering on {json_path} ---")

    with open(json_path, 'r') as f:
        data = json.load(f)

    # Mock Config
    config = {
        "HEURISTICS": {
            "CLUSTERING": {
                "MIN_SAMPLES": 1,
                "MIN_CLUSTER_SIZE": 2
            }
        }
    }

    for page_data in data['pages']:
        print(f"\nProcessing Page {page_data['page_number']}")

        # Test on Left Column Only for demo
        raw_blocks = page_data.get('left_column_blocks', [])
        if not raw_blocks:
            continue

        # Convert JSON dicts back to TextBlock objects
        blocks = [TextBlock(**b) for b in raw_blocks]

        # Sort by Y to ensure correct order for 'previous_block' logic
        blocks.sort(key=lambda b: b.bbox[1])

        print(f"Found {len(blocks)} blocks in left column.")

        # Simulate the Analysis Loop
        previous_block = None

        for i, block in enumerate(blocks):
            # Create Context
            context = AnalysisContext(
                current_block=block,
                previous_block=previous_block,
                all_blocks_in_scope=blocks, # Pass the whole list for the cache logic
                scope_median_spacing=10.0, # Dummy
                scope_min_x=0.0,
                scope_median_font_size=10.0,
                config=config
            )

            # RUN THE HEURISTIC
            result = detect_cluster_break(context)

            # Print results if significant
            if result and result['is_new_cluster']:
                print(f"\n>>> DETECTED CLUSTER BREAK (Conf: {result['confidence']})")
                print(f"    Block: {block.text[:50]}...")
                print(f"    Transition: Cluster {result['prev_cluster_label']} -> {result['cluster_label']}")
            elif result:
                # Optional: Print regular cluster assignment
                # print(f"    Block: {block.text[:20]}... [Cluster: {result['cluster_label']}]")
                pass

            previous_block = block

if __name__ == "__main__":
    # Point this to your actual JSON file
    test_heuristic_on_json("output/01_analyzed_document.json")