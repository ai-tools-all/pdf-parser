"""
OpenAI Vision API OCR Provider Implementation

Uses OpenAI's GPT-4 Vision API for text extraction from images.
This provides high accuracy OCR with understanding of context.

Requirements:
    pip install openai

Environment:
    OPENAI_API_KEY: Your OpenAI API key
"""

import os
import base64
from typing import List, Dict, Any
from PIL import Image
import io

from ..ocr import OCRProvider, OCRResult


class OpenAIOCRProvider(OCRProvider):
    """
    OCR provider using OpenAI Vision API.
    
    Configuration options:
        OCR.OPENAI.api_key: API key (or use OPENAI_API_KEY env var)
        OCR.OPENAI.model: Model to use (default: "gpt-4o-mini")
        OCR.OPENAI.max_tokens: Max tokens for response (default: 4096)
        OCR.OPENAI.detail: Image detail level ("low", "high", "auto") (default: "high")
    
    Note: This provider returns text without exact bounding boxes since
    the Vision API doesn't provide positional information. All results
    have a placeholder bbox.
    """
    
    DEFAULT_SYSTEM_PROMPT = """You are an OCR assistant. Extract all visible text from the image.
Return the text exactly as it appears, preserving:
- Line breaks and paragraph structure
- Numbered lists and bullet points
- Question numbers and answer options (a), (b), (c), (d)

Return ONLY the extracted text, nothing else. Do not add explanations or formatting markers."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize OpenAI Vision API client.
        
        Args:
            config: Configuration dictionary with OCR settings
        """
        self.config = config
        ocr_config = config.get("OCR", {}).get("OPENAI", {})
        
        # Get API key from config or environment
        self.api_key = ocr_config.get("api_key") or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Set OCR.OPENAI.api_key in config "
                "or OPENAI_API_KEY environment variable."
            )
        
        self.model = ocr_config.get("model", "gpt-4o-mini")
        self.max_tokens = ocr_config.get("max_tokens", 4096)
        self.detail = ocr_config.get("detail", "high")
        self.system_prompt = ocr_config.get("system_prompt", self.DEFAULT_SYSTEM_PROMPT)
        
        # Lazy import
        try:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError(
                "OpenAI library not installed. Install with: pip install openai"
            )
        
        self._available = True
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string."""
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
    
    def extract_text(self, image: Image.Image) -> List[OCRResult]:
        """
        Extract text from a PIL Image using OpenAI Vision API.
        
        Args:
            image: PIL Image object
            
        Returns:
            List of OCRResult (single result with full text, no bbox)
        """
        # Convert image to base64
        base64_image = self._image_to_base64(image)
        
        # Make API call
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": self.system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                                "detail": self.detail
                            }
                        }
                    ]
                }
            ],
            max_tokens=self.max_tokens
        )
        
        # Extract text from response
        text = response.choices[0].message.content.strip()
        
        if not text:
            return []
        
        # Split text into lines and create results
        # Since OpenAI doesn't provide bbox, we use sequential y positions
        lines = text.split('\n')
        results = []
        
        line_height = 20  # Approximate line height
        for i, line in enumerate(lines):
            line = line.strip()
            if line:  # Skip empty lines
                results.append(OCRResult(
                    text=line,
                    bbox=(0, i * line_height, image.width, (i + 1) * line_height),
                    confidence=1.0  # OpenAI doesn't provide confidence
                ))
        
        return results
    
    def extract_text_from_bytes(self, image_bytes: bytes) -> List[OCRResult]:
        """
        Extract text from image bytes.
        
        Args:
            image_bytes: Raw image data
            
        Returns:
            List of OCRResult objects
        """
        image = Image.open(io.BytesIO(image_bytes))
        return self.extract_text(image)
    
    @property
    def name(self) -> str:
        return "openai"
    
    def is_available(self) -> bool:
        return self._available
