"""
Nutrition Extractor Module

Extracts food items from transcriptions and calculates nutritional information.
"""

from typing import List, Optional, Tuple
from pydantic import BaseModel, Field, field_validator
from .gemini_helper import get_structured_completion
from .agentic_loop import agentic_loop_with_model


# ==================== PYDANTIC MODELS ====================

class FoodItem(BaseModel):
    """Represents a food item with quantity and preparation details."""

    name: str = Field(description="Name of the food item (e.g., 'cooked rice', 'banana')")
    quantity: float = Field(description="Numeric quantity (e.g., 1.0, 0.5, 2.0)")
    unit: str = Field(description="Unit of measurement (e.g., 'cup', 'piece', 'glass', 'gram')")
    preparation: Optional[str] = Field(
        default=None,
        description="Preparation method if mentioned (e.g., 'steamed', 'cooked', 'raw')"
    )

    @field_validator('quantity')
    @classmethod
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be positive')
        return v

    @field_validator('name')
    @classmethod
    def name_must_be_specific(cls, v):
        # Avoid vague terms
        vague_terms = ['food', 'stuff', 'thing', 'item']
        if v.lower() in vague_terms:
            raise ValueError(f'Food name too vague: {v}')
        return v


class FoodItemList(BaseModel):
    """List of food items extracted from transcription."""

    items: List[FoodItem] = Field(description="List of food items mentioned")


class NutritionInfo(BaseModel):
    """Nutritional information for a food item."""

    calories: float = Field(description="Calories (kcal)")
    protein_g: float = Field(description="Protein in grams")
    carbs_g: float = Field(description="Carbohydrates in grams")
    fat_g: float = Field(description="Fat in grams")
    fiber_g: Optional[float] = Field(default=None, description="Dietary fiber in grams")
    sugar_g: Optional[float] = Field(default=None, description="Sugar in grams")

    @field_validator('calories', 'protein_g', 'carbs_g', 'fat_g')
    @classmethod
    def values_must_be_non_negative(cls, v):
        if v < 0:
            raise ValueError('Nutritional values must be non-negative')
        return v


class FoodItemWithNutrition(BaseModel):
    """Food item combined with its nutritional information."""

    food_item: FoodItem
    nutrition: NutritionInfo


class DailyNutritionSummary(BaseModel):
    """Summary of daily nutritional intake."""

    items: List[FoodItemWithNutrition] = Field(description="All food items with nutrition")
    total_calories: float = Field(description="Total calories for the day")
    total_protein_g: float = Field(description="Total protein in grams")
    total_carbs_g: float = Field(description="Total carbohydrates in grams")
    total_fat_g: float = Field(description="Total fat in grams")
    total_fiber_g: Optional[float] = Field(default=None, description="Total fiber in grams")


# ==================== EXTRACTION FUNCTIONS ====================

def extract_food_items(
    transcription: str,
    api_key: Optional[str] = None,
    use_agentic_loop: bool = True,
) -> List[FoodItem]:
    """
    Extract food items from transcription text using Gemini.

    Args:
        transcription: Text from audio transcription
        api_key: Gemini API key
        use_agentic_loop: Whether to use agentic validation loop (default: True)

    Returns:
        List of extracted FoodItem objects

    Example:
        >>> transcription = "I had one cup of rice and half a banana"
        >>> items = extract_food_items(transcription)
        >>> print(items[0].name, items[0].quantity, items[0].unit)
        rice 1.0 cup
    """

    prompt = f"""Extract all food items from this transcription about nutrition and meals.

Transcription: "{transcription}"

For each food item mentioned, identify:
1. The food name (be specific, include preparation if mentioned)
2. The quantity (convert words like "half" to 0.5, "one" to 1.0)
3. The unit (cup, glass, piece, gram, tablespoon, etc.)
4. The preparation method if mentioned (cooked, steamed, raw, fried, etc.)

Examples:
- "one cup of cooked rice" → name: "rice", quantity: 1.0, unit: "cup", preparation: "cooked"
- "half a banana" → name: "banana", quantity: 0.5, unit: "piece", preparation: null
- "two steamed dumplings" → name: "dumplings", quantity: 2.0, unit: "piece", preparation: "steamed"
- "one glass of milk" → name: "milk", quantity: 1.0, unit: "glass", preparation: null

Extract all food items as a list."""

    if use_agentic_loop:
        # Use agentic loop with validation
        def task_fn(feedback: Optional[str]) -> FoodItemList:
            enhanced_prompt = prompt
            if feedback:
                enhanced_prompt += f"\n\nPrevious attempt had issues: {feedback}\nPlease correct and try again."

            return get_structured_completion(
                enhanced_prompt,
                FoodItemList,
                api_key=api_key,
            )

        def validation_fn(result: FoodItemList) -> Tuple[bool, Optional[str]]:
            """Validate extracted food items."""
            if not result.items:
                return False, "No food items found. Please extract at least one item."

            # Check for suspiciously vague items
            for item in result.items:
                if len(item.name) < 2:
                    return False, f"Food name too short: '{item.name}'"

                # Common unit check
                valid_units = [
                    'cup', 'cups', 'glass', 'glasses', 'piece', 'pieces',
                    'gram', 'grams', 'g', 'kg', 'kilogram', 'kilograms',
                    'tablespoon', 'tablespoons', 'tbsp', 'teaspoon', 'teaspoons', 'tsp',
                    'ounce', 'ounces', 'oz', 'pound', 'pounds', 'lb',
                    'ml', 'milliliter', 'milliliters', 'liter', 'liters', 'l',
                    'bowl', 'bowls', 'plate', 'plates', 'serving', 'servings'
                ]
                if item.unit.lower() not in valid_units:
                    return False, f"Unusual unit '{item.unit}' for {item.name}. Use standard units."

            return True, None

        result = agentic_loop_with_model(
            task_fn=task_fn,
            response_model=FoodItemList,
            custom_validation=validation_fn,
            max_iterations=3,
        )
        return result.items

    else:
        # Direct extraction without loop
        result = get_structured_completion(
            prompt,
            FoodItemList,
            api_key=api_key,
        )
        return result.items


def get_nutrition_info(
    food_item: FoodItem,
    api_key: Optional[str] = None,
) -> NutritionInfo:
    """
    Get nutritional information for a food item using Gemini.

    Args:
        food_item: FoodItem to get nutrition info for
        api_key: Gemini API key

    Returns:
        NutritionInfo with macros adjusted for quantity

    Example:
        >>> item = FoodItem(name="rice", quantity=1.0, unit="cup", preparation="cooked")
        >>> nutrition = get_nutrition_info(item)
        >>> print(nutrition.calories, nutrition.protein_g)
        206 4.3
    """

    # Build description
    description = f"{food_item.quantity} {food_item.unit} of {food_item.name}"
    if food_item.preparation:
        description += f" ({food_item.preparation})"

    prompt = f"""Provide accurate nutritional information for this food item: {description}

Calculate the nutritional values for the EXACT quantity specified.

Food item: {description}

Provide:
- Calories (kcal)
- Protein (grams)
- Carbohydrates (grams)
- Fat (grams)
- Fiber (grams, optional)
- Sugar (grams, optional)

Use standard nutritional databases (USDA, etc.) for accuracy.
Adjust values based on the quantity and unit provided.

For example:
- 1 cup of cooked white rice ≈ 206 calories, 4.3g protein, 45g carbs, 0.4g fat
- 1 medium banana ≈ 105 calories, 1.3g protein, 27g carbs, 0.4g fat
- 1 cup of whole milk ≈ 150 calories, 8g protein, 12g carbs, 8g fat"""

    return get_structured_completion(
        prompt,
        NutritionInfo,
        api_key=api_key,
        temperature=0.2,  # Lower temperature for more consistent nutritional data
    )


def calculate_daily_summary(
    items_with_nutrition: List[FoodItemWithNutrition]
) -> DailyNutritionSummary:
    """
    Calculate total daily nutrition from items.

    Args:
        items_with_nutrition: List of food items with their nutrition info

    Returns:
        DailyNutritionSummary with totals

    Example:
        >>> items = [...]  # List of FoodItemWithNutrition
        >>> summary = calculate_daily_summary(items)
        >>> print(summary.total_calories, summary.total_protein_g)
        1500 65.2
    """

    total_calories = sum(item.nutrition.calories for item in items_with_nutrition)
    total_protein = sum(item.nutrition.protein_g for item in items_with_nutrition)
    total_carbs = sum(item.nutrition.carbs_g for item in items_with_nutrition)
    total_fat = sum(item.nutrition.fat_g for item in items_with_nutrition)

    # Optional totals (only if all items have the value)
    total_fiber = None
    if all(item.nutrition.fiber_g is not None for item in items_with_nutrition):
        total_fiber = sum(item.nutrition.fiber_g for item in items_with_nutrition)

    return DailyNutritionSummary(
        items=items_with_nutrition,
        total_calories=round(total_calories, 1),
        total_protein_g=round(total_protein, 1),
        total_carbs_g=round(total_carbs, 1),
        total_fat_g=round(total_fat, 1),
        total_fiber_g=round(total_fiber, 1) if total_fiber else None,
    )


def process_transcription_to_nutrition(
    transcription: str,
    api_key: Optional[str] = None,
) -> DailyNutritionSummary:
    """
    Complete pipeline: transcription → food items → nutrition → summary.

    Args:
        transcription: Text from audio transcription
        api_key: Gemini API key

    Returns:
        DailyNutritionSummary with all items and totals

    Example:
        >>> transcription = "I had one cup of rice and half a banana"
        >>> summary = process_transcription_to_nutrition(transcription)
        >>> print(f"Total: {summary.total_calories} calories")
    """

    # Step 1: Extract food items
    food_items = extract_food_items(transcription, api_key=api_key)

    # Step 2: Get nutrition for each item
    items_with_nutrition = []
    for food_item in food_items:
        nutrition = get_nutrition_info(food_item, api_key=api_key)
        items_with_nutrition.append(
            FoodItemWithNutrition(
                food_item=food_item,
                nutrition=nutrition
            )
        )

    # Step 3: Calculate summary
    summary = calculate_daily_summary(items_with_nutrition)

    return summary
