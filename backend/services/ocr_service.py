"""
OCR Service - Text extraction from images using TrOCR
Week 1 implementation
"""

from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image
import torch


class OCRService:
    """Service for extracting text from images using TrOCR"""
    
    def __init__(self, model_name="microsoft/trocr-base-printed"):
        """
        Initialize OCR service with TrOCR model
        
        Args:
            model_name: Hugging Face model identifier
        """
        print(f"Loading OCR model: {model_name}...")
        self.processor = TrOCRProcessor.from_pretrained(model_name)
        self.model = VisionEncoderDecoderModel.from_pretrained(model_name)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        print(f"✅ OCR model loaded on {self.device}")
    
    def extract_text(self, image_path):
        """
        Extract text from an image file
        
        Args:
            image_path: Path to image file
            
        Returns:
            str: Extracted text
        """
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
            print(f"❌ OCR Error: {e}")
            raise


# Global instance (lazy loading)
_ocr_service = None


def get_ocr_service():
    """Get or create OCR service instance (singleton)"""
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService()
    return _ocr_service
