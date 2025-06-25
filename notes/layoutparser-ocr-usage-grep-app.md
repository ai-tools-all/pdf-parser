# LayoutParser OCR Usage Guide

## Problem Analysis

The error encountered: `module layoutparser has no attribute TesseractAgent`

**Root Cause**: The TesseractAgent class is in the `layoutparser.ocr` submodule, not directly accessible from the main `layoutparser` module.

## Correct Import Statements

### Option 1: Import from OCR submodule
```python
import layoutparser as lp
from layoutparser.ocr import TesseractAgent, TesseractFeatureType

# Or directly:
from layoutparser import TesseractAgent, TesseractFeatureType
```

### Option 2: Full module import
```python
import layoutparser as lp
# Access via: lp.TesseractAgent() - This should work if properly installed
```

## Installation Requirements

### Basic OCR Support
```bash
pip install "layoutparser[ocr]"
```

### Additional Dependencies
- **Tesseract OCR Engine**: Must be installed separately
  ```bash
  # Ubuntu/Debian
  sudo apt-get install tesseract-ocr-eng
  
  # macOS
  brew install tesseract
  
  # Windows: Download from official repo
  ```

### Python Dependencies
- `pytesseract` - Python wrapper for Tesseract
- `cv2` (OpenCV) - Image processing
- `PIL` (Pillow) - Image handling

## TesseractAgent Usage Examples

### Basic Text Extraction
```python
import layoutparser as lp

# Initialize OCR agent
ocr_agent = lp.TesseractAgent(languages='eng')

# Simple text extraction
text = ocr_agent.detect(image)
print(text)
```

### Advanced Usage with Language Support
```python
# Multiple languages
ocr_agent = lp.TesseractAgent(languages='eng+fra')
# Or as list
ocr_agent = lp.TesseractAgent(languages=['eng', 'fra'])
```

### Custom Tesseract Path
```python
ocr_agent = lp.TesseractAgent.with_tesseract_executable(
    tesseract_cmd_path='/custom/path/to/tesseract',
    languages='eng'
)
```

### OCR with Layout Detection Pipeline
```python
import layoutparser as lp
import cv2
import numpy as np

# Load layout detection model
model = lp.Detectron2LayoutModel(
    'lp://PubLayNet/mask_rcnn_X_101_32x8d_FPN_3x/config',
    extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.8],
    label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"}
)

# Initialize OCR agent
ocr_agent = lp.TesseractAgent(languages='eng')

# Process image
image = cv2.imread('document.jpg')
image = image[..., ::-1]  # BGR to RGB

# Detect layout
layout = model.detect(image)

# Extract text from each detected region
for block in layout:
    if block.type in ['Text', 'Title']:
        # Crop the region with padding
        segment_image = (block
                        .pad(left=5, right=5, top=5, bottom=5)
                        .crop_image(image))
        
        # Extract text
        text = ocr_agent.detect(segment_image)
        
        # Store text in the block
        block.set(text=text, inplace=True)

# Print extracted text
for block in layout:
    if hasattr(block, 'text'):
        print(f"{block.type}: {block.text}")
```

## TesseractAgent Methods

### `detect()` Method Parameters
- `image`: Input image (numpy array or file path)
- `return_response=False`: Return full Tesseract response
- `return_only_text=True`: Return only text string
- `agg_output_level=None`: Aggregate output by level (PAGE, BLOCK, PARA, LINE, WORD)

### Feature Types (TesseractFeatureType)
- `PAGE = 0`: Page level
- `BLOCK = 1`: Block level  
- `PARA = 2`: Paragraph level
- `LINE = 3`: Line level
- `WORD = 4`: Word level

### Advanced Text Extraction
```python
from layoutparser.ocr import TesseractFeatureType

# Get structured data at word level
ocr_result = ocr_agent.detect(
    image, 
    return_only_text=False,
    agg_output_level=TesseractFeatureType.WORD
)
```

## Error Troubleshooting

### Common Issues
1. **TesseractAgent not found**: Check imports and installation
2. **Tesseract executable not found**: Install Tesseract OCR engine
3. **Language data missing**: Install language packs
4. **Image format issues**: Ensure proper image preprocessing

### Debug Installation
```python
from layoutparser.file_utils import is_pytesseract_available
print(f"PyTesseract available: {is_pytesseract_available()}")

# Test basic functionality
try:
    import pytesseract
    print("PyTesseract imported successfully")
    print(f"Tesseract version: {pytesseract.get_tesseract_version()}")
except Exception as e:
    print(f"PyTesseract error: {e}")
```

## Alternative OCR Agents

### Google Cloud Vision
```python
from layoutparser.ocr import GCVAgent, GCVFeatureType

# Requires GCP credentials
gcv_agent = lp.GCVAgent()
text = gcv_agent.detect(image)
```

## Best Practices

1. **Image Preprocessing**: Ensure good image quality for better OCR results
2. **Language Selection**: Specify correct languages for better accuracy
3. **Error Handling**: Always wrap OCR calls in try-catch blocks
4. **Performance**: Consider batch processing for multiple images
5. **Resource Management**: OCR can be memory-intensive for large images

## Fix for Your Code

Replace this line in your `layoutlm_extractor.py`:
```python
# OLD (incorrect)
self.ocr_agent = lp.TesseractAgent(languages='eng')

# NEW (correct)
from layoutparser.ocr import TesseractAgent
self.ocr_agent = TesseractAgent(languages='eng')

# OR (if main import works)
import layoutparser as lp
self.ocr_agent = lp.TesseractAgent(languages='eng')  # Should work with proper installation
```

Make sure you have installed the OCR dependencies:
```bash
pip install "layoutparser[ocr]"
```