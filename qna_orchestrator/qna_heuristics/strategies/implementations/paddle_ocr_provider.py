"""
PaddleOCR Provider Implementation

Uses PaddlePaddle's OCR engine for text extraction from images.
PaddleOCR provides high accuracy and supports multiple languages.

Installation:
    pip install paddlepaddle paddleocr

Note: PaddleOCR downloads models on first use (~300MB).
"""

from typing import List, Dict, Any
from PIL import Image
import io

from ..ocr import OCRProvider, OCRResult


class PaddleOCRProvider(OCRProvider):
    """
    OCR provider using PaddleOCR.
    
    Configuration options:
        OCR.PADDLE.use_angle_cls: Enable text angle detection (default: True)
        OCR.PADDLE.lang: Language code (default: "en")
        OCR.PADDLE.use_gpu: Use GPU acceleration (default: False)
        OCR.PADDLE.show_log: Show PaddleOCR logs (default: False)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize PaddleOCR engine.
        
        Args:
            config: Configuration dictionary with OCR settings
        """
        self.config = config
        ocr_config = config.get("OCR", {}).get("PADDLE", {})
        
        # Lazy import to avoid loading PaddleOCR if not needed
        try:
            from paddleocr import PaddleOCR
        except ImportError:
            raise ImportError(
                "PaddleOCR not installed. Install with: pip install paddlepaddle paddleocr"
            )
        
        self._ocr = PaddleOCR(
            use_angle_cls=ocr_config.get("use_angle_cls", True),
            lang=ocr_config.get("lang", "en"),
            use_gpu=ocr_config.get("use_gpu", False),
            show_log=ocr_config.get("show_log", False),
        )
        self._available = True
    
    def extract_text(self, image: Image.Image) -> List[OCRResult]:
        """
        Extract text from a PIL Image using PaddleOCR.
        
        Args:
            image: PIL Image object
            
        Returns:
            List of OCRResult with text, bounding boxes, and confidence
        """
        import numpy as np
        # Convert PIL Image to numpy array (RGB)
        img_array = np.array(image.convert("RGB"))
        
        # Run OCR
        result = self._ocr.ocr(img_array, cls=True)
        
        ocr_results = []
        
        # PaddleOCR returns: [[[box1, (text, conf)], [box2, (text, conf)], ...]]
        if result and result[0]:
            for line in result[0]:
                box = line[0]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                text_conf = line[1]  # (text, confidence)
                
                if text_conf and len(text_conf) >= 2:
                    text = text_conf[0]
                    confidence = text_conf[1]
                    
                    # Convert 4-point box to x0,y0,x1,y1 format
                    x_coords = [p[0] for p in box]
                    y_coords = [p[1] for p in box]
                    bbox = (min(x_coords), min(y_coords), max(x_coords), max(y_coords))
                    
                    ocr_results.append(OCRResult(
                        text=text.strip(),
                        bbox=bbox,
                        confidence=float(confidence)
                    ))
        
        # Sort by reading order (top-to-bottom, left-to-right)
        ocr_results.sort(key=lambda r: (r.y0, r.x0))
        
        return ocr_results
    
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
        return "paddle"
    
    def is_available(self) -> bool:
        return self._available
