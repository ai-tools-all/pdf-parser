"""
Tests for OCR strategy interface and provider registry.
"""

import pytest
from PIL import Image
import io


class TestOCRInterface:
    """Test OCR strategy interface imports and registry."""
    
    def test_import_ocr_types(self):
        """Test that OCR types can be imported."""
        from qna_orchestrator.qna_heuristics.strategies import (
            OCRProvider,
            OCRResult,
            OCRProviderRegistry,
            get_ocr_provider,
        )
        assert OCRProvider is not None
        assert OCRResult is not None
        assert OCRProviderRegistry is not None
        assert get_ocr_provider is not None
    
    def test_ocr_result_properties(self):
        """Test OCRResult dataclass properties."""
        from qna_orchestrator.qna_heuristics.strategies import OCRResult
        
        result = OCRResult(
            text="Hello World",
            bbox=(10.0, 20.0, 100.0, 40.0),
            confidence=0.95
        )
        
        assert result.text == "Hello World"
        assert result.x0 == 10.0
        assert result.y0 == 20.0
        assert result.x1 == 100.0
        assert result.y1 == 40.0
        assert result.confidence == 0.95
    
    def test_registry_list_providers(self):
        """Test that registered providers are listed."""
        from qna_orchestrator.qna_heuristics.strategies import OCRProviderRegistry
        # Import implementations to trigger registration
        from qna_orchestrator.qna_heuristics.strategies import implementations
        
        providers = OCRProviderRegistry.list_providers()
        
        # At least one provider should be registered
        assert isinstance(providers, list)
        # Both paddle and openai should be registered
        assert "paddle" in providers
        assert "openai" in providers
    
    def test_registry_get_unknown_provider(self):
        """Test that getting unknown provider raises ValueError."""
        from qna_orchestrator.qna_heuristics.strategies import get_ocr_provider
        
        with pytest.raises(ValueError, match="not registered"):
            get_ocr_provider("unknown_provider", {})


class TestOCRConfig:
    """Test OCR configuration."""
    
    def test_default_config_has_ocr_section(self):
        """Test that default config contains OCR section."""
        from qna_orchestrator.qna_heuristics.config import DEFAULT_CONFIG
        
        assert "OCR" in DEFAULT_CONFIG
        ocr_config = DEFAULT_CONFIG["OCR"]
        
        assert "DEFAULT_PROVIDER" in ocr_config
        assert "AUTO_OCR_ENABLED" in ocr_config
        assert "MIN_CONFIDENCE" in ocr_config
        assert "PADDLE" in ocr_config
        assert "OPENAI" in ocr_config
    
    def test_paddle_config_defaults(self):
        """Test PaddleOCR default configuration values."""
        from qna_orchestrator.qna_heuristics.config import DEFAULT_CONFIG
        
        paddle_config = DEFAULT_CONFIG["OCR"]["PADDLE"]
        
        assert paddle_config["use_angle_cls"] is True
        assert paddle_config["lang"] == "en"
        assert paddle_config["use_gpu"] is False
        assert paddle_config["show_log"] is False
    
    def test_openai_config_defaults(self):
        """Test OpenAI default configuration values."""
        from qna_orchestrator.qna_heuristics.config import DEFAULT_CONFIG
        
        openai_config = DEFAULT_CONFIG["OCR"]["OPENAI"]
        
        assert openai_config["model"] == "gpt-4o-mini"
        assert openai_config["max_tokens"] == 4096
        assert openai_config["detail"] == "high"
