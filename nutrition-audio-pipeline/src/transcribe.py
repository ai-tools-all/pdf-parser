"""
Audio Transcription Module

Handles audio transcription using Grok API with nutrition-specific context.
"""

import os
from typing import Optional
import requests
from pathlib import Path


# Nutrition-specific prompt template
NUTRITION_TRANSCRIPTION_PROMPT = """You are transcribing audio about daily nutrition and food intake.
The speaker is describing food items they consumed.

Pay special attention to:
- Food item names (e.g., "cooked rice", "banana", "milk", "dumplings")
- Quantities (e.g., "half", "one glass", "two cups", "150 grams")
- Preparation methods (e.g., "steamed", "cooked", "raw", "fried")
- Measurements (e.g., "cup", "tablespoon", "piece", "glass")

Please transcribe accurately, preserving all details about quantities and food items."""


def transcribe_audio(
    audio_file_path: str,
    api_key: Optional[str] = None,
    model: str = "whisper-large-v3-turbo",
    language: Optional[str] = None,
    add_nutrition_context: bool = True,
) -> str:
    """
    Transcribe audio using Grok API with optional nutrition context.

    Args:
        audio_file_path: Path to audio file (mp3, wav, m4a, etc.)
        api_key: Grok API key (if not provided, uses XAI_API_KEY or GROK_API_KEY env var)
        model: Model to use for transcription (default: whisper-large-v3-turbo)
        language: Optional language code (e.g., "en", "es", "fr")
        add_nutrition_context: Whether to add nutrition-specific prompt (default: True)

    Returns:
        Transcribed text

    Raises:
        FileNotFoundError: If audio file doesn't exist
        ValueError: If API key not found
        Exception: If API request fails

    Example:
        >>> transcription = transcribe_audio("breakfast.mp3")
        >>> print(transcription)
        I had one cup of cooked rice, half a banana, and two steamed dumplings.
    """
    # Validate audio file exists
    audio_path = Path(audio_file_path)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

    # Get API key from parameter or environment
    if api_key is None:
        api_key = os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY")
        if not api_key:
            raise ValueError(
                "API key not found. Set XAI_API_KEY or GROK_API_KEY environment variable, "
                "or pass api_key parameter."
            )

    # Grok API endpoint for audio transcription
    # Using the x.AI API which is compatible with OpenAI's audio endpoint
    api_url = "https://api.x.ai/v1/audio/transcriptions"

    # Prepare the file
    with open(audio_file_path, "rb") as audio_file:
        files = {
            "file": (audio_path.name, audio_file, f"audio/{audio_path.suffix[1:]}")
        }

        # Prepare form data
        data = {
            "model": model,
        }

        # Add optional parameters
        if language:
            data["language"] = language

        if add_nutrition_context:
            data["prompt"] = NUTRITION_TRANSCRIPTION_PROMPT

        # Prepare headers
        headers = {
            "Authorization": f"Bearer {api_key}",
        }

        # Make API request
        try:
            response = requests.post(
                api_url,
                headers=headers,
                files=files,
                data=data,
                timeout=300,  # 5 minute timeout for large files
            )

            # Check for errors
            response.raise_for_status()

            # Parse response
            result = response.json()

            # Extract transcription text
            if "text" in result:
                return result["text"]
            else:
                raise Exception(f"Unexpected API response format: {result}")

        except requests.exceptions.HTTPError as e:
            error_detail = ""
            try:
                error_detail = response.json()
            except:
                error_detail = response.text

            raise Exception(
                f"Grok API request failed with status {response.status_code}: {error_detail}"
            ) from e

        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error during transcription: {str(e)}") from e


def transcribe_audio_fallback(
    audio_file_path: str,
    api_key: Optional[str] = None,
    use_openai: bool = False,
) -> str:
    """
    Fallback transcription using OpenAI Whisper API if Grok is unavailable.

    Args:
        audio_file_path: Path to audio file
        api_key: OpenAI API key (uses OPENAI_API_KEY env var if not provided)
        use_openai: Force use of OpenAI instead of Grok

    Returns:
        Transcribed text
    """
    # Validate audio file exists
    audio_path = Path(audio_file_path)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

    # Get API key
    if api_key is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

    # OpenAI Whisper endpoint
    api_url = "https://api.openai.com/v1/audio/transcriptions"

    # Prepare the file
    with open(audio_file_path, "rb") as audio_file:
        files = {
            "file": (audio_path.name, audio_file, f"audio/{audio_path.suffix[1:]}")
        }

        data = {
            "model": "whisper-1",
            "prompt": NUTRITION_TRANSCRIPTION_PROMPT,
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
        }

        # Make API request
        response = requests.post(
            api_url,
            headers=headers,
            files=files,
            data=data,
            timeout=300,
        )

        response.raise_for_status()
        result = response.json()

        return result["text"]


def transcribe_text_mock(text: str) -> str:
    """
    Mock transcription function for testing without audio files.

    Simply returns the input text as if it were transcribed.
    Useful for development and testing.

    Args:
        text: Text to treat as transcription

    Returns:
        The same text (mocked transcription)

    Example:
        >>> transcription = transcribe_text_mock(
        ...     "I had one cup of rice and half a banana"
        ... )
        >>> print(transcription)
        I had one cup of rice and half a banana
    """
    return text
