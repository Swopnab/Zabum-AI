"""
Zabum AI - Configuration Settings
"""

import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
STORAGE_DIR = PROJECT_ROOT / "storage"
UPLOAD_FOLDER = STORAGE_DIR / "uploads"
THUMBNAIL_FOLDER = STORAGE_DIR / "thumbnails"
DB_PATH = STORAGE_DIR / "zabum.db"

# Ensure directories exist
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
THUMBNAIL_FOLDER.mkdir(parents=True, exist_ok=True)

# AI / Ollama Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama")  # 'ollama', 'mock', etc.

# OCR Configuration
OCR_MODEL_NAME = os.getenv("OCR_MODEL_NAME", "microsoft/trocr-base-printed")

# Allowed upload file extensions
IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "webp"}
DOCUMENT_EXTENSIONS = {
    "txt", "md", "markdown", "py", "js", "ts", "html", "css", "json", "csv", 
    "sql", "sh", "yaml", "yml", "xml", "pdf"
}
ALLOWED_EXTENSIONS = IMAGE_EXTENSIONS.union(DOCUMENT_EXTENSIONS)

MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32 MB max upload

# Context & RAG Parameters
MAX_RECENT_MESSAGES = 10
MAX_RETRIEVED_CHUNKS = 4
MAX_RETRIEVED_MEMORIES = 6
CHUNK_SIZE = 400
CHUNK_OVERLAP = 60

# Central System Prompt
SYSTEM_PROMPT = """You are Zabum AI, a private, intelligent, and highly capable personal AI assistant.

Your core traits:
1. Helpful & Concise: Provide clear, direct, and well-structured answers without unnecessary fluff.
2. Technically Capable: Expert in programming, software architecture, reasoning, analysis, and problem-solving.
3. Conversational & Polite: Engage naturally with the user while maintaining professional quality.
4. Honest & Grounded: If you do not know something or if information is not present in the provided context, state it honestly rather than hallucinating.
5. Personal Context Aware: When user memories or retrieved knowledge/documents are provided, use them seamlessly to personalize and enrich your responses.

Formatting Rules:
- Use GitHub Flavored Markdown for formatting.
- Always use syntax-highlighted code blocks with the appropriate language identifier for code snippets.
- Use bullet points and bold text for readability when explaining multi-part concepts.
"""
