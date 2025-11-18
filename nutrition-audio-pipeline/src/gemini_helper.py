"""
Gemini Helper Module

Provides helper functions for calling Google's Gemini models via LiteLLM
with structured output support using Pydantic models.
"""

import os
from typing import TypeVar, Type, Optional
from pydantic import BaseModel
import litellm
from litellm import completion

# Type variable for Pydantic models
T = TypeVar('T', bound=BaseModel)


def get_structured_completion(
    prompt: str,
    response_model: Type[T],
    model: str = "gemini/gemini-1.5-flash",
    api_key: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: Optional[int] = None,
    max_retries: int = 3,
) -> T:
    """
    Call Gemini via LiteLLM and get structured output conforming to a Pydantic model.

    Args:
        prompt: The input prompt/question for the LLM
        response_model: Pydantic model class that defines the expected output structure
        model: LiteLLM model identifier (default: gemini/gemini-1.5-flash)
        api_key: Gemini API key (if not provided, uses GEMINI_API_KEY env var)
        temperature: Sampling temperature (0.0-1.0, lower = more deterministic)
        max_tokens: Maximum tokens in response (None = model default)
        max_retries: Number of retry attempts on failure

    Returns:
        Instance of response_model populated with LLM's structured output

    Raises:
        Exception: If all retry attempts fail

    Example:
        >>> class Person(BaseModel):
        ...     name: str
        ...     age: int
        >>> result = get_structured_completion(
        ...     "Extract person info: John is 25 years old",
        ...     Person
        ... )
        >>> print(result.name, result.age)
        John 25
    """
    # Get API key from parameter or environment
    if api_key is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

    # Set the API key for litellm
    os.environ["GEMINI_API_KEY"] = api_key

    # Build messages
    messages = [{"role": "user", "content": prompt}]

    # Prepare kwargs
    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }

    if max_tokens:
        kwargs["max_tokens"] = max_tokens

    # Attempt completion with retries
    last_exception = None
    for attempt in range(max_retries):
        try:
            # Call LiteLLM completion
            response = completion(**kwargs)

            # Extract content from response
            content = response.choices[0].message.content

            # Parse JSON content into Pydantic model
            # LiteLLM returns JSON string, so we parse it
            import json

            # Try to parse as JSON first
            try:
                if isinstance(content, str):
                    data = json.loads(content)
                else:
                    data = content

                # Create and validate Pydantic model
                result = response_model.model_validate(data)
                return result

            except json.JSONDecodeError:
                # If not JSON, try to extract JSON from markdown code blocks
                import re
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(1))
                    result = response_model.model_validate(data)
                    return result
                else:
                    # Last resort: assume the content itself is the data
                    result = response_model.model_validate_json(content)
                    return result

        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                # Wait before retry (exponential backoff)
                import time
                time.sleep(2 ** attempt)
                continue
            else:
                # Final attempt failed
                break

    # All retries exhausted
    raise Exception(f"Failed to get structured completion after {max_retries} attempts: {last_exception}")


def get_simple_completion(
    prompt: str,
    model: str = "gemini/gemini-1.5-flash",
    api_key: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    system_prompt: Optional[str] = None,
) -> str:
    """
    Call Gemini via LiteLLM and get a simple text response.

    Args:
        prompt: The input prompt/question for the LLM
        model: LiteLLM model identifier (default: gemini/gemini-1.5-flash)
        api_key: Gemini API key (if not provided, uses GEMINI_API_KEY env var)
        temperature: Sampling temperature (0.0-1.0)
        max_tokens: Maximum tokens in response (None = model default)
        system_prompt: Optional system prompt to set context

    Returns:
        String response from the LLM

    Example:
        >>> response = get_simple_completion("What is the capital of France?")
        >>> print(response)
        The capital of France is Paris.
    """
    # Get API key from parameter or environment
    if api_key is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

    # Set the API key for litellm
    os.environ["GEMINI_API_KEY"] = api_key

    # Build messages
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    # Prepare kwargs
    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }

    if max_tokens:
        kwargs["max_tokens"] = max_tokens

    # Call LiteLLM completion
    response = completion(**kwargs)

    # Extract and return content
    return response.choices[0].message.content


def get_json_completion(
    prompt: str,
    model: str = "gemini/gemini-1.5-flash",
    api_key: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: Optional[int] = None,
) -> dict:
    """
    Call Gemini via LiteLLM and get a JSON response.

    This is a convenience function that requests JSON output and parses it.
    For strict schema validation, use get_structured_completion with a Pydantic model.

    Args:
        prompt: The input prompt/question for the LLM
        model: LiteLLM model identifier
        api_key: Gemini API key
        temperature: Sampling temperature
        max_tokens: Maximum tokens in response

    Returns:
        Parsed JSON dictionary
    """
    # Enhance prompt to request JSON
    enhanced_prompt = f"{prompt}\n\nRespond with valid JSON only."

    # Get text response
    response_text = get_simple_completion(
        enhanced_prompt,
        model=model,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens
    )

    # Parse JSON
    import json
    import re

    # Try direct parse
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        # Try to extract from code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        else:
            raise ValueError(f"Could not parse JSON from response: {response_text}")
