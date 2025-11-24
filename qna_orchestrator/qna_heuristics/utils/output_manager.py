import os
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

class OutputManager:
    def __init__(self, base_output_dir: str, input_pdf_path: str, config: Dict):
        self.config = config
        
        # 1. Create Session Directory
        pdf_name = Path(input_pdf_path).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = Path(base_output_dir) / f"{timestamp}_{pdf_name}"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        # 2. Setup Logging
        self.logger = self._setup_logging()
        self.logger.info(f"Session initialized at: {self.session_dir}")

        # 3. Track Timing
        self.start_time = time.time()

    def _setup_logging(self):
        """Configures logging to file and console."""
        logger = logging.getLogger("PDFParser")
        logger.setLevel(logging.DEBUG)
        logger.handlers = []  # Clear existing

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        # File Handler (Always Verbose)
        fh = logging.FileHandler(self.session_dir / "parser.log", encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        # Console Handler (Optional based on config)
        if self.config.get("ENABLE_CONSOLE_LOGGING", True):
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            ch.setFormatter(formatter)
            logger.addHandler(ch)

        return logger

    def save_json(self, data: Any, filename: str):
        """Saves data to the session directory."""
        # Custom encoder for dataclasses
        class DataClassEncoder(json.JSONEncoder):
            def default(self, o):
                if hasattr(o, '__dict__'):
                    return o.__dict__
                return super().default(o)

        filepath = self.session_dir / filename
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, cls=DataClassEncoder, indent=2, ensure_ascii=False)
            self.logger.info(f"Saved output: {filename}")
        except Exception as e:
            self.logger.error(f"Failed to save {filename}: {e}")

    def save_metadata(self, stats: Dict[str, Any]):
        """Saves run metadata, config, and stats."""
        duration = time.time() - self.start_time
        
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": round(duration, 2),
            "output_directory": str(self.session_dir),
            "run_stats": stats,
            "configuration": self.config
        }
        
        self.save_json(metadata, "metadata.json")
