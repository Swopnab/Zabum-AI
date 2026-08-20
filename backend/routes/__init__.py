"""
Routes package for Zabum AI
"""
from routes.chat import chat_bp
from routes.conversations import conversations_bp
from routes.memory import memory_bp
from routes.documents import documents_bp
from routes.status import status_bp

__all__ = [
    "chat_bp",
    "conversations_bp",
    "memory_bp",
    "documents_bp",
    "status_bp",
]
