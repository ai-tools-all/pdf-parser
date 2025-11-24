"""
OCR Strategy Interface

Defines the protocol for OCR providers that can extract text from images.
Different implementations support various backends:
- PaddleOCR: Fast, accurate, runs locally
- OpenAI Vision API: Cloud-based, high accuracy
- Tesseract: Traditional OCR engine

The OCR system integrates with the extraction pipeline to handle
image-based PDF pages where native text extraction yields no results.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass
from PIL import Image
import io


@dataclass
class OCRResult:
    """
    Result from OCR processing containing text and position info.
    
    Attributes:
        text: Extracted text string
        bbox: Bounding box (x0, y0, x1, y1) in image coordinates
        confidence: Confidence score (0.0 to 1.0)
    """
    text: str
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1)
    confidence: float = 1.0
    
    @property
    def x0(self) -> float:
        return self.bbox[0]
    
    @property
    def y0(self) -> float:
        return self.bbox[1]
    
    @property
    def x1(self) -> float:
        return self.bbox[2]
    
    @property
    def y1(self) -> float:
        return self.bbox[3]


class OCRProvider(ABC):
    """
    Abstract base class for OCR providers.
    
    Implementations should handle initialization of their specific
    OCR engine and provide text extraction from PIL Images.
    
    Usage:
        provider = PaddleOCRProvider(config)
        results = provider.extract_text(image)
        for result in results:
            print(f"{result.text} at {result.bbox} ({result.confidence:.2f})")
    """
    
    @abstractmethod
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the OCR provider with configuration.
        
        Args:
            config: Configuration dictionary with provider-specific settings
        """
        ...
    
    @abstractmethod
    def extract_text(self, image: Image.Image) -> List[OCRResult]:
        """
        Extract text from a PIL Image.
        
        Args:
            image: PIL Image object to process
            
        Returns:
            List of OCRResult objects with extracted text and positions
        """
        ...
    
    @abstractmethod
    def extract_text_from_bytes(self, image_bytes: bytes) -> List[OCRResult]:
        """
        Extract text from image bytes.
        
        Args:
            image_bytes: Raw image data (PNG, JPEG, etc.)
            
        Returns:
            List of OCRResult objects with extracted text and positions
        """
        ...
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider name for logging/debugging."""
        ...
    
    def is_available(self) -> bool:
        """
        Check if the OCR provider is available and properly configured.
        
        Returns:
            True if the provider can be used, False otherwise
        """
        return True


class OCRProviderRegistry:
    """
    Registry for OCR providers.
    
    Allows registering and retrieving OCR provider implementations by name.
    
    Usage:
        registry = OCRProviderRegistry()
        registry.register("paddle", PaddleOCRProvider)
        provider = registry.get("paddle", config)
    """
    
    _providers: Dict[str, type] = {}
    
    @classmethod
    def register(cls, name: str, provider_class: type):
        """
        Register an OCR provider class.
        
        Args:
            name: Provider name (e.g., "paddle", "openai", "tesseract")
            provider_class: Class implementing OCRProvider
        """
        cls._providers[name] = provider_class
    
    @classmethod
    def get(cls, name: str, config: Dict[str, Any]) -> OCRProvider:
        """
        Get an instance of a registered OCR provider.
        
        Args:
            name: Provider name
            config: Configuration dictionary
            
        Returns:
            Initialized OCRProvider instance
            
        Raises:
            ValueError: If provider is not registered
        """
        if name not in cls._providers:
            available = ", ".join(cls._providers.keys()) or "none"
            raise ValueError(
                f"OCR provider '{name}' not registered. Available: {available}"
            )
        return cls._providers[name](config)
    
    @classmethod
    def list_providers(cls) -> List[str]:
        """Return list of registered provider names."""
        return list(cls._providers.keys())


def get_ocr_provider(name: str, config: Dict[str, Any]) -> OCRProvider:
    """
    Convenience function to get an OCR provider by name.
    
    Args:
        name: Provider name ("paddle", "openai", etc.)
        config: Configuration dictionary
        
    Returns:
        Initialized OCRProvider instance
    """
    return OCRProviderRegistry.get(name, config)
