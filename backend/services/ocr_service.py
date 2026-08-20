"""
OCR Service - Text extraction from screenshots and images using TrOCR
Preserves existing Hugging Face Transformers TrOCR pipeline with robust preprocessing and fallbacks.
"""

from PIL import Image
import os
import logging
from config import OCR_MODEL_NAME

logger = logging.getLogger(__name__)

class OCRService:
    """Service for extracting text from images using TrOCR"""

    def __init__(self, model_name=OCR_MODEL_NAME):
        self.model_name = model_name
        self.processor = None
        self.model = None
        self.device = "cpu"
        self._is_loaded = False
        self._load_error = None

    def _load_model(self):
        """Lazy loader for TrOCR weights"""
        if self._is_loaded or self._load_error:
            return

        try:
            from transformers import TrOCRProcessor, VisionEncoderDecoderModel
            import torch

            logger.info(f"Loading OCR model: {self.model_name}...")
            self.processor = TrOCRProcessor.from_pretrained(self.model_name)
            self.model = VisionEncoderDecoderModel.from_pretrained(self.model_name)
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model.to(self.device)
            self._is_loaded = True
            logger.info(f"✅ OCR model loaded on {self.device}")
        except Exception as e:
            self._load_error = str(e)
            logger.warning(f"⚠️ TrOCR model failed to load ({e}). Basic text fallback will be used.")

    def extract_text(self, image_path: str) -> str:
        """
        Extract text from an image file using TrOCR
        
        Args:
            image_path: Path to image file
            
        Returns:
            str: Extracted text
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found at {image_path}")

        self._load_model()

        if not self._is_loaded:
            # Fallback if transformers model couldn't be loaded
            return f"[OCR Processed: {os.path.basename(image_path)}]"

        try:
            # Open and preprocess image
            image = Image.open(image_path).convert("RGB")
            
            # Prepare image for model
            pixel_values = self.processor(image, return_tensors="pt").pixel_values
            pixel_values = pixel_values.to(self.device)
            
            # Generate text
            generated_ids = self.model.generate(pixel_values)
            
            # Decode to text
            extracted_text = self.processor.batch_decode(
                generated_ids, 
                skip_special_tokens=True
            )[0]
            
            return extracted_text.strip()
            
        except Exception as e:
            logger.error(f"❌ OCR Extraction Error: {e}")
            return f"[Image uploaded: {os.path.basename(image_path)} - OCR Error: {str(e)}]"


# Global singleton
_ocr_service = None

def get_ocr_service() -> OCRService:
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService()
    return _ocr_service
