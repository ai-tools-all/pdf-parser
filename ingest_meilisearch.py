#!/usr/bin/env python3
"""
Meilisearch Ingestion Script for MCQ Data

Install meilisearch-python client first:
pip install meilisearch

Usage:
python ingest_meilisearch.py output/merged_forum/20251125_023932_PTS-2025-GS-Simulator-Test-0-QP-Eng-Hindi-1_modified_odd/final_exam_merged.json
"""

import json
import sys
import os
import hashlib
from typing import List, Dict, Any
from meilisearch import Client


def load_mcq_data(json_path: str) -> List[Dict[str, Any]]:
    """Load MCQ data from JSON file."""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_question_hash(mcq: Dict[str, Any]) -> str:
    """Generate a unique hash for the question based on its content."""
    # Create a string combining question text and options for hashing
    content = mcq['question_text']
    if 'options' in mcq:
        options_str = json.dumps(mcq['options'], sort_keys=True)
        content += options_str

    # Generate SHA256 hash
    return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]  # Use first 16 chars for shorter ID


def prepare_documents(mcqs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Prepare MCQ documents for Meilisearch indexing."""
    documents = []
    for mcq in mcqs:
        # Flatten the options for better searchability
        options_text = " ".join([f"{k}: {v}" for k, v in mcq.get('options', {}).items()])

        # Generate unique ID based on question content
        question_id = generate_question_hash(mcq)

        doc = {
            'id': question_id,
            'question_number': mcq['question_number'],
            'question_text': mcq['question_text'],
            'options': mcq.get('options', {}),
            'options_text': options_text,  # Combined options for search
            'answer': mcq.get('answer', ''),
            'explanation': mcq.get('explanation', ''),
            # Add searchable content combining question and options
            'searchable_content': f"{mcq['question_text']} {options_text}"
        }
        documents.append(doc)

    return documents


def ingest_to_meilisearch(json_path: str, meili_url: str = 'http://localhost:7700',
                         api_key: str = '', index_name: str = 'mcq_questions'):
    """
    Ingest MCQ data from JSON file into Meilisearch.

    Args:
        json_path: Path to the JSON file containing MCQ data
        meili_url: Meilisearch server URL
        api_key: Meilisearch API key (optional)
        index_name: Name of the index to create/use
    """
    # Initialize Meilisearch client
    client = Client(meili_url, api_key)

    # Load and prepare data
    print(f"Loading data from {json_path}...")
    mcqs = load_mcq_data(json_path)
    documents = prepare_documents(mcqs)

    print(f"Found {len(documents)} questions to index")

    # Create or get index
    try:
        index = client.get_index(index_name)
        print(f"Using existing index: {index_name}")
    except:
        # Create index and wait for it to be ready
        task = client.create_index(index_name)
        client.wait_for_task(task.task_uid)
        index = client.get_index(index_name)
        print(f"Created new index: {index_name}")

    # Configure searchable attributes
    task = index.update_searchable_attributes([
        'question_text',
        'options_text',
        'explanation',
        'searchable_content'
    ])
    client.wait_for_task(task.task_uid)

    # Configure filterable attributes
    task = index.update_filterable_attributes([
        'question_number',
        'answer'
    ])
    client.wait_for_task(task.task_uid)

    # Add documents to index
    print("Indexing documents...")
    result = index.add_documents(documents)

    print(f"Indexing task created with ID: {result.task_uid}")

    # Wait for indexing to complete
    print("Waiting for indexing to complete...")
    client.wait_for_task(result.task_uid)

    print("✅ Successfully ingested MCQ data into Meilisearch!")


def main():
    if len(sys.argv) != 2:
        print("Usage: python ingest_meilisearch.py <path_to_json_file>")
        sys.exit(1)

    json_path = sys.argv[1]

    if not os.path.exists(json_path):
        print(f"Error: File {json_path} does not exist")
        sys.exit(1)

    # You can modify these defaults or make them configurable
    MEILI_URL = os.getenv('MEILI_URL', 'http://localhost:7700')
    MEILI_API_KEY = os.getenv('MEILI_MASTER_KEY', 'aSampleMasterKey')  # Default master key

    ingest_to_meilisearch(json_path, MEILI_URL, MEILI_API_KEY)


if __name__ == '__main__':
    main()