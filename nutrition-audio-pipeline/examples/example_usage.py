"""
Example Usage of Nutrition Audio Pipeline

This file demonstrates various ways to use the nutrition audio pipeline.
"""

import os
import sys

# Add parent directory to path to import src modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.pipeline import (
    process_nutrition_audio,
    process_text_nutrition,
    print_summary,
    save_summary_json,
)


def example_1_audio_processing():
    """
    Example 1: Process audio file with Grok transcription.

    Prerequisites:
    - Audio file exists
    - XAI_API_KEY environment variable set
    - GEMINI_API_KEY environment variable set
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: Full Audio Processing")
    print("="*70)

    # Process audio file
    summary = process_nutrition_audio(
        audio_file_path="breakfast.mp3",
        verbose=True
    )

    # Save to JSON
    save_summary_json(summary, "nutrition_log.json")


def example_2_text_processing():
    """
    Example 2: Process text directly (no audio file needed).

    Prerequisites:
    - GEMINI_API_KEY environment variable set
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: Text-Only Processing (No Audio)")
    print("="*70)

    # Define food intake as text
    text = """
    For breakfast today, I had one cup of cooked white rice,
    half a banana, one glass of banana shake made with milk,
    and two steamed dumplings.
    """

    # Process text
    summary = process_text_nutrition(
        text=text,
        verbose=True
    )

    # Can also print summary separately
    print_summary(summary, detailed=True)


def example_3_multiple_meals():
    """
    Example 3: Process multiple meals separately and combine.
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: Multiple Meals")
    print("="*70)

    meals = {
        "breakfast": "Two eggs, one slice of whole wheat toast, and a glass of orange juice",
        "lunch": "Grilled chicken breast 150 grams, one cup of brown rice, and steamed broccoli",
        "dinner": "Salmon fillet 200 grams, half cup of quinoa, and mixed salad",
        "snacks": "One apple, handful of almonds about 30 grams"
    }

    all_summaries = []

    for meal_name, meal_text in meals.items():
        print(f"\n--- Processing {meal_name.upper()} ---")

        summary = process_text_nutrition(
            text=meal_text,
            verbose=False
        )

        all_summaries.append(summary)

        print(f"{meal_name.capitalize()}: {summary.total_calories} kcal, "
              f"{summary.total_protein_g}g protein")

    # Calculate day totals
    total_calories = sum(s.total_calories for s in all_summaries)
    total_protein = sum(s.total_protein_g for s in all_summaries)
    total_carbs = sum(s.total_carbs_g for s in all_summaries)
    total_fat = sum(s.total_fat_g for s in all_summaries)

    print("\n" + "="*70)
    print("FULL DAY TOTALS")
    print("="*70)
    print(f"Total Calories:   {total_calories} kcal")
    print(f"Total Protein:    {total_protein} g")
    print(f"Total Carbs:      {total_carbs} g")
    print(f"Total Fat:        {total_fat} g")
    print("="*70)


def example_4_custom_api_keys():
    """
    Example 4: Provide API keys programmatically instead of environment variables.
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: Custom API Keys")
    print("="*70)

    # You can pass API keys directly
    summary = process_text_nutrition(
        text="One cup of oatmeal with honey and berries",
        gemini_api_key="your-gemini-api-key-here",
        verbose=True
    )


def example_5_error_handling():
    """
    Example 5: Proper error handling.
    """
    print("\n" + "="*70)
    print("EXAMPLE 5: Error Handling")
    print("="*70)

    try:
        # This will fail if API key not set
        summary = process_text_nutrition(
            text="One apple",
            verbose=True
        )
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("💡 Make sure GEMINI_API_KEY is set in your environment")

    except Exception as e:
        print(f"❌ Unexpected Error: {e}")


def example_6_minimal_usage():
    """
    Example 6: Minimal usage - just the essentials.
    """
    print("\n" + "="*70)
    print("EXAMPLE 6: Minimal Usage")
    print("="*70)

    # Simplest possible usage
    summary = process_text_nutrition(
        "I ate two slices of pizza and drank one can of cola",
        verbose=False
    )

    # Quick access to totals
    print(f"Calories: {summary.total_calories}")
    print(f"Protein: {summary.total_protein_g}g")
    print(f"Carbs: {summary.total_carbs_g}g")
    print(f"Fat: {summary.total_fat_g}g")

    # Access individual items
    for item in summary.items:
        print(f"- {item.food_item.name}: {item.nutrition.calories} cal")


def main():
    """
    Main function to run examples.

    Uncomment the example you want to run.
    """

    # Check if API key is set
    if not os.getenv("GEMINI_API_KEY"):
        print("⚠️  WARNING: GEMINI_API_KEY not found in environment variables")
        print("Set it in your .env file or export it:")
        print("  export GEMINI_API_KEY='your-key-here'")
        print()

    # Run examples (uncomment the ones you want)

    # example_1_audio_processing()  # Requires audio file + both API keys
    example_2_text_processing()     # Only requires Gemini API key
    # example_3_multiple_meals()
    # example_4_custom_api_keys()
    # example_5_error_handling()
    # example_6_minimal_usage()


if __name__ == "__main__":
    main()
