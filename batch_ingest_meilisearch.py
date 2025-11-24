#!/usr/bin/env python3
"""
Batch Meilisearch Ingestion Script for All final_exam_merged.json Files

This script finds all final_exam_merged.json files in the output directory,
adds source folder path metadata, and ingests them into Meilisearch.

Usage:
python batch_ingest_meilisearch.py [output_dir]

Default output_dir: output/
"""

import json
import sys
import os
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from meilisearch import Client


def find_final_exam_files(output_dir: str = "output") -> List[Path]:
    """Find all final_exam_merged.json files in the output directory."""
    output_path = Path(output_dir)
    if not output_path.exists():
        raise FileNotFoundError(f"Output directory {output_dir} does not exist")

    # Find all final_exam_merged.json files
    pattern = "**/final_exam_merged.json"
    files = list(output_path.glob(pattern))

    print(f"Found {len(files)} final_exam_merged.json files:")
    for file_path in files:
        print(f"  - {file_path}")

    return files


def generate_question_hash(mcq: Dict[str, Any]) -> str:
    """Generate a unique hash for the question based on question text only."""
    content = mcq['question_text']
    return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]


def load_metadata(json_file: Path) -> Optional[Dict[str, Any]]:
    """Load metadata.json from the same folder as the json file."""
    metadata_path = json_file.parent / "metadata.json"
    if metadata_path.exists():
        with open(metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def prepare_documents_with_source(mcqs: List[Dict[str, Any]], source_path: str, 
                                   metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Prepare MCQ documents for Meilisearch indexing with source and metadata."""
    documents = []
    for mcq in mcqs:
        # Flatten the options for better searchability
        options_text = " ".join([f"{k}: {v}" for k, v in mcq.get('options', {}).items()])

        # Generate unique ID based on question text only
        question_id = generate_question_hash(mcq)

        doc = {
            'id': question_id,
            'question_number': mcq['question_number'],
            'question_text': mcq['question_text'],
            'options': mcq.get('options', {}),
            'options_text': options_text,
            'answer': mcq.get('answer', ''),
            'explanation': mcq.get('explanation', ''),
            'searchable_content': f"{mcq['question_text']} {options_text}",
            'source_folder': source_path,
            'source_type': 'final_exam_merged'
        }
        
        # Merge metadata if available
        if metadata:
            if 'timestamp' in metadata:
                doc['metadata_timestamp'] = metadata['timestamp']
            if 'run_stats' in metadata:
                run_stats = metadata['run_stats']
                doc['questions_found'] = run_stats.get('questions_found')
                doc['solutions_found'] = run_stats.get('solutions_found')
                doc['merged_count'] = run_stats.get('merged_count')
                if 'inputs' in run_stats:
                    doc['question_file'] = run_stats['inputs'].get('question_file', '')
                    doc['solution_file'] = run_stats['inputs'].get('solution_file', '')
        
        documents.append(doc)

    return documents


def load_mcq_data(json_path: Path) -> List[Dict[str, Any]]:
    """Load MCQ data from JSON file."""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def batch_ingest_to_meilisearch(json_files: List[Path], base_dir: Path,
                               meili_url: str = 'http://localhost:7700',
                               api_key: str = 'aSampleMasterKey', index_name: str = 'mcq_questions'):
    """
    Batch ingest multiple final_exam_merged.json files into Meilisearch.

    Args:
        json_files: List of paths to final_exam_merged.json files
        base_dir: Base directory for computing relative source paths
        meili_url: Meilisearch server URL
        api_key: Meilisearch API key
        index_name: Name of the index to create/use
    """
    # Initialize Meilisearch client
    client = Client(meili_url, api_key)

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
        'searchable_content',
        'source_folder'
    ])
    client.wait_for_task(task.task_uid)

    # Configure filterable attributes
    task = index.update_filterable_attributes([
        'question_number',
        'answer',
        'source_folder',
        'source_type'
    ])
    client.wait_for_task(task.task_uid)

    total_questions = 0
    successful_files = 0
    failed_files = 0

    # Process each file
    for i, json_file in enumerate(json_files, 1):
        try:
            print(f"\n[{i}/{len(json_files)}] Processing: {json_file}")

            # Load data
            mcqs = load_mcq_data(json_file)
            print(f"  Loaded {len(mcqs)} questions")

            # Load metadata if available
            metadata = load_metadata(json_file)
            if metadata:
                print(f"  Loaded metadata from metadata.json")

            # Get source folder path (relative to base directory)
            try:
                source_folder = str(json_file.parent.relative_to(base_dir))
            except ValueError:
                source_folder = str(json_file.parent)

            # Prepare documents with source and metadata
            documents = prepare_documents_with_source(mcqs, source_folder, metadata)

            # Add documents to index
            print(f"  Indexing {len(documents)} documents...")
            result = index.add_documents(documents)

            # Wait for indexing to complete
            client.wait_for_task(result.task_uid)

            total_questions += len(documents)
            successful_files += 1
            print(f"  ✅ Successfully indexed {len(documents)} questions from {source_folder}")

        except Exception as e:
            print(f"  ❌ Failed to process {json_file}: {str(e)}")
            failed_files += 1
            continue

    print("\n🎉 Batch ingestion completed!")
    print(f"  Total files processed: {len(json_files)}")
    print(f"  Successful: {successful_files}")
    print(f"  Failed: {failed_files}")
    print(f"  Total questions indexed: {total_questions}")


def main():
    # Parse command line arguments
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "output"
    base_dir = Path(output_dir).resolve()

    print(f"Starting batch ingestion from directory: {output_dir}")

    try:
        # Find all final_exam_merged.json files
        json_files = find_final_exam_files(output_dir)

        if not json_files:
            print("No final_exam_merged.json files found. Nothing to ingest.")
            return

        # Get Meilisearch configuration from environment
        MEILI_URL = os.getenv('MEILI_URL', 'http://localhost:7700')
        MEILI_API_KEY = os.getenv('MEILI_MASTER_KEY', 'aSampleMasterKey')

        print(f"Meilisearch URL: {MEILI_URL}")
        print(f"Index: mcq_questions")

        # Perform batch ingestion
        batch_ingest_to_meilisearch(json_files, base_dir, MEILI_URL, MEILI_API_KEY)

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()