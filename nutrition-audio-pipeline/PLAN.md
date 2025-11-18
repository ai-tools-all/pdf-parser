# Nutrition Audio Pipeline - Design Plan

## Overview
A Python-based system that processes audio recordings of food items and extracts nutritional information for daily macro tracking (carbs, proteins, fats, etc.).

## Pipeline Flow

```
Audio Input
    ↓
1. TRANSCRIPTION (Grok API)
    - Send audio file to Grok
    - Add nutrition context to prompt
    - Get text transcription
    ↓
2. ITEM EXTRACTION (Gemini + Structured Output)
    - Parse transcription
    - Extract food items with quantities
    - Use agentic loop for validation
    ↓
3. NUTRITION LOOKUP (Gemini + Structured Output)
    - Get nutritional values for each item
    - Calculate macros (carbs, proteins, fats, calories)
    - Adjust for quantities
    ↓
4. OUTPUT
    - Daily nutrition summary
    - Per-item breakdown
```

## Project Structure

```
nutrition-audio-pipeline/
├── pyproject.toml              # uv project config
├── README.md                   # Usage instructions
├── PLAN.md                     # This file
├── src/
│   ├── gemini_helper.py        # LiteLLM + Gemini structured outputs
│   ├── agentic_loop.py         # Agentic for loop implementation
│   ├── transcribe.py           # Grok API audio transcription
│   ├── nutrition_extractor.py  # Extract nutrition info
│   └── pipeline.py             # Main orchestrator
├── examples/
│   ├── example_usage.py        # Usage examples
│   └── sample_audio/           # Sample audio files (if any)
└── tests/                      # Unit tests (optional)
```

## Components

### 1. Gemini Helper (`gemini_helper.py`)
**Purpose**: Wrapper around LiteLLM for calling Gemini with structured outputs

**Key Functions**:
- `get_structured_completion(prompt, response_model, model="gemini/gemini-1.5-pro")`
  - Takes a prompt and Pydantic model
  - Returns structured output conforming to the model
  - Handles retries and errors

**Dependencies**:
- litellm
- pydantic

### 2. Agentic For Loop (`agentic_loop.py`)
**Purpose**: Implements a self-correcting loop using LLM feedback

**Key Functions**:
- `agentic_loop(initial_input, validation_fn, max_iterations=5)`
  - Runs LLM in a loop
  - Validates output using validation_fn
  - Re-prompts with feedback until valid or max iterations
  - Returns final result or raises error

**Use Cases**:
- Validate extracted food items make sense
- Ensure quantities are properly parsed
- Verify nutritional calculations

### 3. Audio Transcription (`transcribe.py`)
**Purpose**: Call Grok API to transcribe audio with nutrition context

**Key Functions**:
- `transcribe_audio(audio_file_path, api_key=None)`
  - Sends audio to Grok API
  - Includes nutrition-specific prompt
  - Returns transcription text

**Prompt Template**:
```
You are transcribing audio about daily nutrition and food intake.
The speaker is describing food items they consumed.
Pay special attention to:
- Food item names (e.g., "cooked rice", "banana", "milk")
- Quantities (e.g., "half", "one glass", "two cups")
- Preparation methods (e.g., "steamed", "cooked", "raw")

Please transcribe accurately.
```

**API Details**:
- Endpoint: Grok audio transcription API
- Input: Audio file (MP3, WAV, etc.)
- Output: Text transcription

### 4. Nutrition Extractor (`nutrition_extractor.py`)
**Purpose**: Extract food items and calculate nutritional macros

**Key Classes** (Pydantic models):

```python
class FoodItem(BaseModel):
    name: str                    # e.g., "cooked rice"
    quantity: float              # e.g., 1.0
    unit: str                    # e.g., "cup", "piece", "glass"
    preparation: Optional[str]   # e.g., "steamed", "cooked"

class NutritionInfo(BaseModel):
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: Optional[float]

class FoodItemWithNutrition(BaseModel):
    food_item: FoodItem
    nutrition: NutritionInfo

class DailyNutritionSummary(BaseModel):
    items: List[FoodItemWithNutrition]
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
```

**Key Functions**:
- `extract_food_items(transcription: str) -> List[FoodItem]`
  - Uses Gemini to parse transcription
  - Returns structured food items
  - Uses agentic loop for validation

- `get_nutrition_info(food_item: FoodItem) -> NutritionInfo`
  - Calls Gemini to get nutritional values
  - Adjusts for quantity and unit
  - Returns macro breakdown

- `calculate_daily_summary(items: List[FoodItemWithNutrition]) -> DailyNutritionSummary`
  - Aggregates all items
  - Calculates totals
  - Returns summary

### 5. Main Pipeline (`pipeline.py`)
**Purpose**: Orchestrate the entire workflow

**Key Function**:
```python
def process_nutrition_audio(
    audio_file_path: str,
    grok_api_key: str,
    gemini_api_key: str
) -> DailyNutritionSummary:
    # 1. Transcribe audio
    transcription = transcribe_audio(audio_file_path, grok_api_key)

    # 2. Extract food items (with agentic loop)
    food_items = extract_food_items(transcription)

    # 3. Get nutrition info for each item
    items_with_nutrition = [
        FoodItemWithNutrition(
            food_item=item,
            nutrition=get_nutrition_info(item)
        )
        for item in food_items
    ]

    # 4. Calculate summary
    summary = calculate_daily_summary(items_with_nutrition)

    return summary
```

## Example Usage

```python
from pipeline import process_nutrition_audio

# Process an audio recording
summary = process_nutrition_audio(
    audio_file_path="breakfast.mp3",
    grok_api_key="xai-...",
    gemini_api_key="AIza..."
)

# Print results
print(f"Total Calories: {summary.total_calories}")
print(f"Total Protein: {summary.total_protein_g}g")
print(f"Total Carbs: {summary.total_carbs_g}g")
print(f"Total Fat: {summary.total_fat_g}g")

print("\nItems:")
for item in summary.items:
    food = item.food_item
    nutrition = item.nutrition
    print(f"- {food.quantity} {food.unit} {food.name}: "
          f"{nutrition.calories} cal, "
          f"{nutrition.protein_g}g protein, "
          f"{nutrition.carbs_g}g carbs")
```

## Example Input/Output

**Input Audio Transcript**:
> "Today for breakfast I had one cup of cooked rice, half a banana, one glass of banana shake made with milk, and two steamed dumplings"

**Output**:
```json
{
  "items": [
    {
      "food_item": {
        "name": "cooked rice",
        "quantity": 1.0,
        "unit": "cup",
        "preparation": "cooked"
      },
      "nutrition": {
        "calories": 206,
        "protein_g": 4.3,
        "carbs_g": 45.0,
        "fat_g": 0.4
      }
    },
    {
      "food_item": {
        "name": "banana",
        "quantity": 0.5,
        "unit": "piece",
        "preparation": null
      },
      "nutrition": {
        "calories": 53,
        "protein_g": 0.6,
        "carbs_g": 13.5,
        "fat_g": 0.2
      }
    },
    {
      "food_item": {
        "name": "banana shake",
        "quantity": 1.0,
        "unit": "glass",
        "preparation": "made with milk"
      },
      "nutrition": {
        "calories": 190,
        "protein_g": 8.0,
        "carbs_g": 30.0,
        "fat_g": 3.5
      }
    },
    {
      "food_item": {
        "name": "steamed dumplings",
        "quantity": 2.0,
        "unit": "piece",
        "preparation": "steamed"
      },
      "nutrition": {
        "calories": 160,
        "protein_g": 6.0,
        "carbs_g": 24.0,
        "fat_g": 4.0
      }
    }
  ],
  "total_calories": 609,
  "total_protein_g": 18.9,
  "total_carbs_g": 112.5,
  "total_fat_g": 8.1
}
```

## Dependencies

```toml
[project]
dependencies = [
    "litellm>=1.0.0",      # LLM abstraction layer
    "pydantic>=2.0.0",     # Data validation
    "requests>=2.31.0",    # HTTP requests for Grok API
    "python-dotenv>=1.0.0" # Environment variables
]
```

## Environment Variables

```bash
GROK_API_KEY=xai-...
GEMINI_API_KEY=AIza...
```

## Agentic Loop Details

The agentic loop is used in food item extraction:

1. **Initial Extraction**: Parse transcription → get food items
2. **Validation**: Check if items make sense (valid foods, reasonable quantities)
3. **Feedback**: If validation fails, provide feedback to LLM
4. **Retry**: Re-extract with feedback incorporated
5. **Max Iterations**: Stop after 5 attempts or when valid

**Validation Rules**:
- Each item has a name, quantity, and unit
- Quantities are positive numbers
- Units are standard (cup, glass, piece, gram, etc.)
- Food names are specific (not vague like "food" or "stuff")

## API Integration Notes

### Grok API
- Endpoint: To be confirmed (likely `https://api.x.ai/v1/audio/transcriptions`)
- Authentication: API key in header
- Input: Multipart form with audio file
- Output: JSON with transcription text

### Gemini via LiteLLM
- Model: `gemini/gemini-1.5-pro` or `gemini/gemini-1.5-flash`
- Structured outputs: Use `response_format` with JSON schema
- Authentication: API key via environment or parameter

## Future Enhancements

1. **Database Storage**: Save daily nutrition logs to SQLite
2. **Batch Processing**: Handle multiple audio files
3. **Voice Detection**: Split long audio into individual food mentions
4. **Custom Food Database**: Learn user's common foods
5. **Meal Categorization**: Breakfast, lunch, dinner, snacks
6. **Nutritional Goals**: Track against daily targets
7. **Web Interface**: Simple UI for upload and viewing results

## Testing Strategy

1. **Unit Tests**: Test each component independently
2. **Mock Audio**: Use text input for testing without audio files
3. **Sample Data**: Create test cases with known nutritional values
4. **Integration Test**: End-to-end test with sample audio

## Success Criteria

- ✅ Audio is successfully transcribed with Grok
- ✅ Food items are accurately extracted from transcription
- ✅ Quantities and units are correctly parsed
- ✅ Nutritional values are reasonable and accurate
- ✅ Total macros are calculated correctly
- ✅ Output is structured and easy to consume

## Timeline

1. Day 1: Core infrastructure (gemini_helper, agentic_loop)
2. Day 2: Transcription + extraction
3. Day 3: Nutrition lookup + pipeline
4. Day 4: Testing + examples
5. Day 5: Documentation + refinement
