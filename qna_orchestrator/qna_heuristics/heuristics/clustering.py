# in heuristics/clustering.py
import numpy as np
from sklearn.cluster import HDBSCAN
from typing import Dict, Any, Optional
from qna_orchestrator.qna_heuristics.data_models import AnalysisContext

# A simple cache to store clustering results per page/column scope to avoid re-running
# Key: id of the first block in scope (unique enough for column scope), Value: Dict[block_id, label]
_CLUSTERING_CACHE = {}

def _run_hdbscan_on_scope(blocks, config):
    """
    Internal helper to run HDBSCAN on a list of blocks.
    Returns a dictionary mapping block_id -> cluster_label.
    """
    if not blocks:
        return {}
    
    # HDBSCAN requires at least 2 samples. If we have 1 or fewer blocks,
    # assign them all to cluster 0 (single cluster)
    if len(blocks) == 1:
        return {blocks[0].id: 0}

    # Extract Y-coordinates (using center_y) for 1D clustering
    # We reshape to (-1, 1) because sklearn expects 2D array
    # We multiply by a factor if needed, but raw coordinates usually work for HDBSCAN
    data = np.array([[(b.bbox[1] + b.bbox[3]) / 2] for b in blocks])

    # Get config parameters or defaults
    cluster_cfg = config.get("HEURISTICS", {}).get("CLUSTERING", {})
    min_cluster_size = cluster_cfg.get("MIN_CLUSTER_SIZE", 2)
    min_samples = cluster_cfg.get("MIN_SAMPLES", 1)

    # Initialize HDBSCAN
    # metric='manhattan' (L1) is often good for 1D vertical spacing
    clusterer = HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric='manhattan'
    )

    labels = clusterer.fit_predict(data)

    # Map results back to block IDs
    return {block.id: int(label) for block, label in zip(blocks, labels)}

def detect_cluster_break(context: AnalysisContext) -> Optional[Dict[str, Any]]:
    """
    Heuristic that uses HDBSCAN to detect if the current block is the start
    of a new spatial cluster (Question/Section).
    """
    blocks_in_scope = context.all_blocks_in_scope
    if not blocks_in_scope:
        return None

    # 1. Check Cache / Run Clustering
    # We use the ID of the first block in the scope as a cache key for this specific column
    scope_key = blocks_in_scope[0].id

    if scope_key not in _CLUSTERING_CACHE:
        _CLUSTERING_CACHE[scope_key] = _run_hdbscan_on_scope(blocks_in_scope, context.config)

    cluster_map = _CLUSTERING_CACHE[scope_key]

    # 2. Get info for current and previous blocks
    current_id = context.current_block.id
    current_label = cluster_map.get(current_id, -1)

    # -1 indicates "noise" in HDBSCAN. We generally ignore noise for start detection
    # unless we want to treat noise as a separator.
    if current_label == -1:
        return {
            "heuristic_name": "hdbscan_clustering",
            "cluster_label": -1,
            "is_new_cluster": False,
            "confidence": 0.0
        }

    prev_label = -1
    if context.previous_block:
        prev_label = cluster_map.get(context.previous_block.id, -1)

    # 3. Determine if this is a start of a new cluster
    # It is a start if:
    # a) There is no previous block (start of page/column)
    # b) The previous block belonged to a different cluster (and wasn't just noise)

    is_new_cluster = False
    if context.previous_block is None:
        is_new_cluster = True
    elif current_label != prev_label:
        is_new_cluster = True

    confidence = 0.0
    if is_new_cluster:
        # High confidence if we moved from one valid cluster to another
        if prev_label != -1:
            confidence = 0.85
        # Lower confidence if we moved from noise to a cluster
        else:
            confidence = 0.6

    return {
        "heuristic_name": "hdbscan_clustering",
        "cluster_label": current_label,
        "prev_cluster_label": prev_label,
        "is_new_cluster": is_new_cluster,
        "confidence": confidence
    }