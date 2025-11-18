"""
Agentic Loop Module

Implements a self-correcting loop pattern where an LLM attempts a task,
validates its output, and retries with feedback until successful or max iterations reached.
"""

from typing import Callable, TypeVar, Any, Optional, Tuple
from pydantic import BaseModel, ValidationError
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type variable for return types
T = TypeVar('T')


class LoopResult(BaseModel):
    """Result of an agentic loop execution."""
    success: bool
    result: Any
    iterations: int
    error: Optional[str] = None


def agentic_loop(
    task_fn: Callable[[Optional[str]], T],
    validation_fn: Callable[[T], Tuple[bool, Optional[str]]],
    max_iterations: int = 5,
    initial_feedback: Optional[str] = None,
    verbose: bool = True
) -> T:
    """
    Execute a task in an agentic loop with validation and feedback.

    The loop works as follows:
    1. Execute task_fn (optionally with feedback from previous iteration)
    2. Validate the result using validation_fn
    3. If valid, return result
    4. If invalid, pass validation feedback to task_fn and retry
    5. Repeat until valid or max_iterations reached

    Args:
        task_fn: Function that performs the task. Takes optional feedback string.
                 Should return the task result.
        validation_fn: Function that validates the result.
                      Returns (is_valid, feedback_message) tuple.
        max_iterations: Maximum number of attempts (default: 5)
        initial_feedback: Optional feedback for first iteration
        verbose: Whether to log progress (default: True)

    Returns:
        The validated result from task_fn

    Raises:
        Exception: If max iterations reached without valid result

    Example:
        >>> def extract_number(feedback=None):
        ...     # LLM extracts number from text
        ...     return {"number": 42}
        >>>
        >>> def validate_number(result):
        ...     if "number" not in result:
        ...         return False, "Missing 'number' field"
        ...     if result["number"] < 0:
        ...         return False, "Number must be positive"
        ...     return True, None
        >>>
        >>> result = agentic_loop(extract_number, validate_number)
        >>> print(result)
        {'number': 42}
    """
    feedback = initial_feedback
    last_error = None

    for iteration in range(1, max_iterations + 1):
        if verbose:
            logger.info(f"Agentic loop iteration {iteration}/{max_iterations}")
            if feedback:
                logger.info(f"Feedback: {feedback}")

        try:
            # Execute the task (with feedback if available)
            result = task_fn(feedback)

            if verbose:
                logger.info(f"Task executed, validating result...")

            # Validate the result
            is_valid, validation_feedback = validation_fn(result)

            if is_valid:
                if verbose:
                    logger.info(f"✓ Validation passed on iteration {iteration}")
                return result
            else:
                # Validation failed, prepare feedback for next iteration
                feedback = validation_feedback or "Validation failed, please try again."
                if verbose:
                    logger.warning(f"✗ Validation failed: {feedback}")
                last_error = feedback

        except Exception as e:
            # Task execution failed
            error_msg = f"Task execution error: {str(e)}"
            if verbose:
                logger.error(error_msg)
            feedback = error_msg
            last_error = str(e)

        # If this was the last iteration, break
        if iteration >= max_iterations:
            break

    # Max iterations reached without success
    error_msg = f"Agentic loop failed after {max_iterations} iterations. Last error: {last_error}"
    if verbose:
        logger.error(error_msg)
    raise Exception(error_msg)


def agentic_loop_with_model(
    task_fn: Callable[[Optional[str]], Any],
    response_model: type[BaseModel],
    custom_validation: Optional[Callable[[BaseModel], Tuple[bool, Optional[str]]]] = None,
    max_iterations: int = 5,
    initial_feedback: Optional[str] = None,
    verbose: bool = True
) -> BaseModel:
    """
    Execute an agentic loop with Pydantic model validation.

    This is a specialized version of agentic_loop that automatically validates
    against a Pydantic model and optionally applies custom validation logic.

    Args:
        task_fn: Function that performs the task. Should return dict or model instance.
        response_model: Pydantic model class to validate against
        custom_validation: Optional additional validation function
        max_iterations: Maximum number of attempts
        initial_feedback: Optional feedback for first iteration
        verbose: Whether to log progress

    Returns:
        Validated Pydantic model instance

    Example:
        >>> class FoodItem(BaseModel):
        ...     name: str
        ...     quantity: float
        ...     unit: str
        >>>
        >>> def extract_food(feedback=None):
        ...     # LLM extracts food item
        ...     return {"name": "rice", "quantity": 1.0, "unit": "cup"}
        >>>
        >>> def validate_food(item):
        ...     if item.quantity <= 0:
        ...         return False, "Quantity must be positive"
        ...     return True, None
        >>>
        >>> result = agentic_loop_with_model(
        ...     extract_food,
        ...     FoodItem,
        ...     validate_food
        ... )
    """

    def validation_fn(result: Any) -> Tuple[bool, Optional[str]]:
        """Combined validation: schema + custom logic."""

        # First, ensure result matches Pydantic model
        try:
            if isinstance(result, dict):
                validated_model = response_model.model_validate(result)
            elif isinstance(result, response_model):
                validated_model = result
            else:
                return False, f"Result must be dict or {response_model.__name__} instance"
        except ValidationError as e:
            # Pydantic validation failed
            error_details = "; ".join([f"{err['loc']}: {err['msg']}" for err in e.errors()])
            return False, f"Schema validation failed: {error_details}"

        # If custom validation provided, apply it
        if custom_validation:
            return custom_validation(validated_model)

        # No custom validation, already valid
        return True, None

    # Run the agentic loop
    result = agentic_loop(
        task_fn=task_fn,
        validation_fn=validation_fn,
        max_iterations=max_iterations,
        initial_feedback=initial_feedback,
        verbose=verbose
    )

    # Ensure return is a model instance
    if isinstance(result, dict):
        return response_model.model_validate(result)
    return result


def simple_retry_loop(
    task_fn: Callable[[], T],
    max_attempts: int = 3,
    verbose: bool = False
) -> T:
    """
    Simple retry loop without validation feedback.

    Attempts to execute task_fn up to max_attempts times.
    Returns first successful result or raises last exception.

    Args:
        task_fn: Function to execute (takes no arguments)
        max_attempts: Maximum number of attempts
        verbose: Whether to log attempts

    Returns:
        Result from task_fn

    Raises:
        Exception: Last exception if all attempts fail
    """
    last_exception = None

    for attempt in range(1, max_attempts + 1):
        try:
            if verbose:
                logger.info(f"Attempt {attempt}/{max_attempts}")

            result = task_fn()

            if verbose:
                logger.info(f"✓ Success on attempt {attempt}")

            return result

        except Exception as e:
            last_exception = e
            if verbose:
                logger.warning(f"✗ Attempt {attempt} failed: {str(e)}")

            if attempt >= max_attempts:
                break

    # All attempts failed
    raise Exception(f"All {max_attempts} attempts failed. Last error: {last_exception}")
