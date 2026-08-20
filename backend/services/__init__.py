"""
Services package for Zabum AI
"""
from services.ai_provider import get_ai_provider, OllamaProvider, MockProvider
from services.ocr_service import get_ocr_service
from services.rag_service import get_rag_service
from services.memory_service import get_memory_service

# Backward compatibility for old llm_service
from services.ai_provider import get_ai_provider as get_llm_service

__all__ = [
    "get_ai_provider",
    "get_llm_service",
    "get_ocr_service",
    "get_rag_service",
    "get_memory_service",
    "OllamaProvider",
    "MockProvider",
]
