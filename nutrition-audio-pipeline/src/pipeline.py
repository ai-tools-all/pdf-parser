"""
Nutrition Audio Pipeline

Main orchestrator that combines audio transcription and nutrition extraction
into a complete end-to-end pipeline.
"""

import os
from typing import Optional
from pathlib import Path
import json

from .transcribe import transcribe_audio, transcribe_text_mock
from .nutrition_extractor import (
    extract_food_items,
    get_nutrition_info,
    calculate_daily_summary,
    FoodItemWithNutrition,
    DailyNutritionSummary,
)


def process_nutrition_audio(
    audio_file_path: str,
    grok_api_key: Optional[str] = None,
    gemini_api_key: Optional[str] = None,
    verbose: bool = True,
) -> DailyNutritionSummary:
    """
    Complete end-to-end pipeline: Audio → Transcription → Nutrition Analysis.

    This is the main function that orchestrates the entire workflow:
    1. Transcribe audio using Grok API
    2. Extract food items from transcription using Gemini
    3. Get nutritional information for each item
    4. Calculate daily summary

    Args:
        audio_file_path: Path to audio file (mp3, wav, m4a, etc.)
        grok_api_key: Grok/X.AI API key (uses XAI_API_KEY env var if not provided)
        gemini_api_key: Gemini API key (uses GEMINI_API_KEY env var if not provided)
        verbose: Whether to print progress messages (default: True)

    Returns:
        DailyNutritionSummary with all items and nutritional totals

    Raises:
        FileNotFoundError: If audio file doesn't exist
        ValueError: If API keys not found
        Exception: If any step in the pipeline fails

    Example:
        >>> summary = process_nutrition_audio("breakfast.mp3")
        >>> print(f"Total calories: {summary.total_calories}")
        >>> print(f"Total protein: {summary.total_protein_g}g")
    """

    if verbose:
        print("=" * 60)
        print("NUTRITION AUDIO PIPELINE")
        print("=" * 60)

    # Step 1: Transcribe audio
    if verbose:
        print("\n[1/4] Transcribing audio...")

    transcription = transcribe_audio(
        audio_file_path=audio_file_path,
        api_key=grok_api_key,
        add_nutrition_context=True,
    )

    if verbose:
        print(f"✓ Transcription complete: \"{transcription}\"")

    # Step 2: Extract food items
    if verbose:
        print("\n[2/4] Extracting food items from transcription...")

    food_items = extract_food_items(
        transcription=transcription,
        api_key=gemini_api_key,
        use_agentic_loop=True,
    )

    if verbose:
        print(f"✓ Found {len(food_items)} food items:")
        for item in food_items:
            prep = f" ({item.preparation})" if item.preparation else ""
            print(f"  - {item.quantity} {item.unit} of {item.name}{prep}")

    # Step 3: Get nutrition info for each item
    if verbose:
        print("\n[3/4] Fetching nutritional information...")

    items_with_nutrition = []
    for idx, food_item in enumerate(food_items, 1):
        if verbose:
            print(f"  [{idx}/{len(food_items)}] Analyzing {food_item.name}...")

        nutrition = get_nutrition_info(
            food_item=food_item,
            api_key=gemini_api_key,
        )

        items_with_nutrition.append(
            FoodItemWithNutrition(
                food_item=food_item,
                nutrition=nutrition
            )
        )

        if verbose:
            print(f"      → {nutrition.calories} cal, "
                  f"{nutrition.protein_g}g protein, "
                  f"{nutrition.carbs_g}g carbs, "
                  f"{nutrition.fat_g}g fat")

    # Step 4: Calculate summary
    if verbose:
        print("\n[4/4] Calculating daily summary...")

    summary = calculate_daily_summary(items_with_nutrition)

    if verbose:
        print("✓ Summary complete!")
        print("\n" + "=" * 60)
        print("DAILY NUTRITION SUMMARY")
        print("=" * 60)
        print(f"Total Calories:   {summary.total_calories} kcal")
        print(f"Total Protein:    {summary.total_protein_g} g")
        print(f"Total Carbs:      {summary.total_carbs_g} g")
        print(f"Total Fat:        {summary.total_fat_g} g")
        if summary.total_fiber_g:
            print(f"Total Fiber:      {summary.total_fiber_g} g")
        print("=" * 60)

    return summary


def process_text_nutrition(
    text: str,
    gemini_api_key: Optional[str] = None,
    verbose: bool = True,
) -> DailyNutritionSummary:
    """
    Process nutrition from text (without audio transcription).

    Useful for testing or when you already have text input.

    Args:
        text: Text describing food items
        gemini_api_key: Gemini API key
        verbose: Whether to print progress

    Returns:
        DailyNutritionSummary

    Example:
        >>> text = "I ate one cup of rice and half a banana"
        >>> summary = process_text_nutrition(text)
    """

    if verbose:
        print("=" * 60)
        print("NUTRITION TEXT PIPELINE")
        print("=" * 60)
        print(f"\nInput text: \"{text}\"")

    # Extract food items
    if verbose:
        print("\n[1/3] Extracting food items...")

    food_items = extract_food_items(
        transcription=text,
        api_key=gemini_api_key,
        use_agentic_loop=True,
    )

    if verbose:
        print(f"✓ Found {len(food_items)} food items")

    # Get nutrition info
    if verbose:
        print("\n[2/3] Fetching nutritional information...")

    items_with_nutrition = []
    for food_item in food_items:
        nutrition = get_nutrition_info(
            food_item=food_item,
            api_key=gemini_api_key,
        )
        items_with_nutrition.append(
            FoodItemWithNutrition(
                food_item=food_item,
                nutrition=nutrition
            )
        )

    # Calculate summary
    if verbose:
        print("\n[3/3] Calculating summary...")

    summary = calculate_daily_summary(items_with_nutrition)

    if verbose:
        print("✓ Complete!")
        print_summary(summary)

    return summary


def print_summary(summary: DailyNutritionSummary, detailed: bool = True):
    """
    Pretty-print a nutrition summary.

    Args:
        summary: DailyNutritionSummary to print
        detailed: Whether to include per-item breakdown (default: True)
    """

    print("\n" + "=" * 60)
    print("DAILY NUTRITION SUMMARY")
    print("=" * 60)

    if detailed:
        print("\nItems:")
        for idx, item in enumerate(summary.items, 1):
            food = item.food_item
            nutrition = item.nutrition

            prep = f" ({food.preparation})" if food.preparation else ""
            print(f"\n{idx}. {food.quantity} {food.unit} of {food.name}{prep}")
            print(f"   Calories:  {nutrition.calories} kcal")
            print(f"   Protein:   {nutrition.protein_g} g")
            print(f"   Carbs:     {nutrition.carbs_g} g")
            print(f"   Fat:       {nutrition.fat_g} g")
            if nutrition.fiber_g:
                print(f"   Fiber:     {nutrition.fiber_g} g")

    print("\n" + "-" * 60)
    print("TOTALS")
    print("-" * 60)
    print(f"Total Calories:   {summary.total_calories} kcal")
    print(f"Total Protein:    {summary.total_protein_g} g")
    print(f"Total Carbs:      {summary.total_carbs_g} g")
    print(f"Total Fat:        {summary.total_fat_g} g")
    if summary.total_fiber_g:
        print(f"Total Fiber:      {summary.total_fiber_g} g")
    print("=" * 60)


def save_summary_json(summary: DailyNutritionSummary, output_path: str):
    """
    Save nutrition summary to JSON file.

    Args:
        summary: DailyNutritionSummary to save
        output_path: Path to output JSON file

    Example:
        >>> save_summary_json(summary, "nutrition_log.json")
    """

    output_file = Path(output_path)
    with open(output_file, 'w') as f:
        json.dump(summary.model_dump(), f, indent=2)

    print(f"✓ Summary saved to {output_path}")


def load_summary_json(input_path: str) -> DailyNutritionSummary:
    """
    Load nutrition summary from JSON file.

    Args:
        input_path: Path to JSON file

    Returns:
        DailyNutritionSummary loaded from file
    """

    with open(input_path, 'r') as f:
        data = json.load(f)

    return DailyNutritionSummary.model_validate(data)
